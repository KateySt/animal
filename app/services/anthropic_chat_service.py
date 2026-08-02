import json
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.anthropic import generate_summary, generate_title, serialize_content_block, serialize_transcript, stream
from app.core.config import get_anthropic_config
from app.db import MessageRole
from app.db.enums import InvoiceStatus
from app.db.models import Animal, ChatSession, HealthLog
from app.db.models.invoice import Invoice
from app.db.models.user import User
from app.schemas.chat import AnimalToolData, HealthLogToolData, InvoiceToolData
from app.services.chat_session_service import ChatSessionService


class AnthropicChatService:
    def __init__(self, session: AsyncSession, session_service: ChatSessionService) -> None:
        self._session = session
        self._session_service = session_service

    async def get_invoices_tool(self, user: User, args: dict[str, Any]) -> str:
        now = datetime.now(UTC).date()
        start = date.fromisoformat(args["start_date"]) if "start_date" in args else now.replace(day=1)
        end = date.fromisoformat(args["end_date"]) if "end_date" in args else now

        query = (
            select(Invoice)
            .where(Invoice.user_id == user.id)
            .where(Invoice.created_at >= datetime(start.year, start.month, start.day, tzinfo=UTC))
            .where(Invoice.created_at <= datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=UTC))
            .options(
                joinedload(Invoice.animal).options(selectinload(Animal.translations)),
                selectinload(Invoice.health_logs).options(selectinload(HealthLog.translations)),
            )
        )
        if "status" in args:
            query = query.where(Invoice.status == InvoiceStatus(args["status"]))

        result = await self._session.execute(query)
        invoices = result.scalars().all()

        items = [
            InvoiceToolData(
                status=invoice.status,
                amount=invoice.to_float(invoice.currency),
                currency=invoice.currency,
                animal=AnimalToolData(
                    gender=invoice.animal.gender,
                    birth_date=invoice.animal.birth_date,
                    translations=invoice.animal.translations,
                ),
                health_log=[HealthLogToolData(translations=log.translations) for log in invoice.health_logs],
            ).model_dump(mode="json")
            for invoice in invoices
        ]

        return json.dumps({"invoices": items, "total": round(sum(i["amount"] for i in items), 2)})

    async def _post_message_hooks(self, chat_session: ChatSession, user_content: str) -> None:
        if chat_session.title is None:
            chat_session.title = await generate_title(user_content)
            await self._session.commit()

        user_count = await self._session_service.count_user_messages(chat_session.id)
        if user_count % get_anthropic_config().SUMMARY_EVERY_N == 0:
            new_rows = await self._session_service.get_messages_since_summary(chat_session.id,
                                                                       chat_session.last_summarized_message_id)
            if new_rows:
                summary = await generate_summary(chat_session.summary, serialize_transcript(new_rows))
                last_id = await self._session_service.get_last_message_id(chat_session.id)
                await self._session_service.set_summary(chat_session, summary, last_id)

    async def stream_response(self, session_id: UUID, user_content: str, user: User) -> AsyncGenerator[str, None]:
        chat_session = await self._session_service.get_session(session_id)
        self._session_service.check_session_owner(chat_session.user_id, user)
        await self._session_service.create_message(session_id, MessageRole.user, user_content)

        messages = await self._session_service.get_messages_for_anthropic(session_id, chat_session.summary)

        tool_was_called = False
        final_message = None

        try:
            async with stream(messages) as active_stream:
                async for event in active_stream:
                    if event.type == "content_block_delta" and event.delta.type == "text_delta":
                        yield event.delta.text
                    elif event.type == "content_block_start" and event.content_block.type == "tool_use":
                        tool_was_called = True

                final_message = await active_stream.get_final_message()

        except Exception as error:
            yield f"[error: streaming failed]{error}"
            return

        if final_message:
            await self._session_service.create_message(
                chat_session.id, MessageRole.assistant,
                [serialize_content_block(block) for block in final_message.content]
            )
            await self._post_message_hooks(chat_session, user_content)

        if tool_was_called and final_message:
            tool_use_block = next(block for block in final_message.content if block.type == "tool_use")

            tool_input = tool_use_block.input

            try:
                tool_result_string = await self.get_invoices_tool(user, tool_input)
            except Exception as error:
                tool_result_string = str(error)

            tool_result_content = [
                {"type": "tool_result", "tool_use_id": tool_use_block.id, "content": tool_result_string}]
            await self._session_service.create_message(session_id, MessageRole.user, tool_result_content, is_tool=True)

            updated_messages = await self._session_service.get_messages_for_anthropic(session_id, chat_session.summary)

            try:
                async with stream(updated_messages) as second_stream:
                    async for chunk in second_stream.text_stream:
                        yield chunk

                    final_message = await second_stream.get_final_message()
                if final_message:
                    await self._session_service.create_message(
                        chat_session.id, MessageRole.assistant,
                        [serialize_content_block(block) for block in final_message.content]
                    )

            except Exception as error:
                yield f"[error: final streaming failed]{error}"
                return
