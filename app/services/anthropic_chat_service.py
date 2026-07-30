import json
from collections.abc import AsyncGenerator, Sequence
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

import anthropic
from anthropic.types import MessageParam
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core import ValidationError, get_anthropic_config
from app.core.error_codes import ErrorCode
from app.core.exceptions import NotFoundError
from app.core.prompts import SYSTEM_PROMPT
from app.core.prompts.system_prompt import TITLE_PROMPT, SUMMARY_PROMPT
from app.core.tools.definitions import TOOL_DEFINITIONS
from app.db import MessageRole
from app.db.enums import InvoiceStatus
from app.db.models import Animal, ChatMessage, ChatSession, HealthLog
from app.db.models.invoice import Invoice
from app.db.models.user import User
from app.schemas.chat import AnimalToolData, HealthLogToolData, InvoiceToolData

client = anthropic.AsyncAnthropic(api_key=get_anthropic_config().ANTHROPIC_API_KEY)


class AnthropicChatService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(self, user: User) -> ChatSession:
        new_session = ChatSession(user_id=user.id, messages=[])
        self._session.add(new_session)
        await self._session.commit()
        await self._session.refresh(new_session)
        return new_session

    async def get_user_sessions(self, user: User) -> Sequence[ChatSession]:
        result = await self._session.execute(select(ChatSession).where(ChatSession.user_id == user.id))
        return result.scalars().all()

    async def get_session_with_messages(self, session_id: UUID) -> ChatSession:
        result = await self._session.execute(
            select(ChatSession).where(ChatSession.id == session_id).options(selectinload(ChatSession.messages)))
        chat_session = result.scalar_one_or_none()
        if chat_session is None:
            raise NotFoundError(ErrorCode.CHAT_SESSION_NOT_FOUND)
        return chat_session

    async def get_session(self, session_id: UUID) -> ChatSession:
        result = await self._session.execute(select(ChatSession).where(ChatSession.id == session_id))
        chat_session = result.scalar_one_or_none()
        if chat_session is None:
            raise NotFoundError(ErrorCode.CHAT_SESSION_NOT_FOUND)
        return chat_session

    async def get_messages_for_anthropic(self, session_id: UUID, summary: str | None = None) -> list[MessageParam]:
        rows = await self._session.execute(
            select(ChatMessage.role, ChatMessage.content)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(get_anthropic_config().RECENT_WINDOW)
        )
        recent = list(reversed([MessageParam(role=role, content=content) for role, content in rows]))
        if summary:
            prefix = [
                MessageParam(role="user", content=f"<conversation_summary>{summary}</conversation_summary>"),
                MessageParam(role="assistant", content="Understood. I have the conversation context from the summary."),
            ]
            return prefix + recent
        return recent

    @staticmethod
    def check_session_owner(session_owner_id: UUID, user: User) -> None:
        if session_owner_id != user.id:
            raise ValidationError(ErrorCode.CHAT_OWNER_NOT_MATCH)

    async def delete_session(self, session_id: UUID, user: User) -> None:
        chat_session = await self.get_session(session_id)
        self.check_session_owner(chat_session.user_id, user)
        await self._session.delete(chat_session)
        await self._session.commit()

    async def create_message(self, session_id: UUID, role: MessageRole, content: Any, is_tool: bool = False) -> None:
        message = ChatMessage(session_id=session_id, role=role, content=content, is_tool=is_tool)
        self._session.add(message)
        await self._session.commit()

    async def count_messages(self, session_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count()).where(ChatMessage.session_id == session_id)
        )
        return result.scalar_one()

    @staticmethod
    async def generate_title(first_message: str) -> str:
        response = await client.messages.create(
            model=get_anthropic_config().ANTHROPIC_MODEL,
            max_tokens=get_anthropic_config().ANTHROPIC_TITLE_MAX_TOKEN,
            system=TITLE_PROMPT,
            messages=[{"role": MessageRole.user, "content": first_message}],
        )
        return response.content[0].text.strip()[:255]

    async def generate_summary(self, session_id: UUID) -> str:
        rows = await self._session.execute(
            select(ChatMessage.role, ChatMessage.content)
            .where(ChatMessage.session_id == session_id)
            .where(ChatMessage.is_tool == False)
            .order_by(ChatMessage.created_at.asc())
        )
        transcript = "\n".join(
            f"{role}: {content if isinstance(content, str) else json.dumps(content)}"
            for role, content in rows
        )
        response = await client.messages.create(
            model=get_anthropic_config().ANTHROPIC_MODEL,
            max_tokens=get_anthropic_config().ANTHROPIC_SUMMERY_MAX_TOKEN,
            system=SUMMARY_PROMPT,
            messages=[{"role": MessageRole.user, "content": transcript}],
        )
        return response.content[0].text.strip()

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

    @staticmethod
    def _get_stream(messages: list[MessageParam]):
        return client.messages.stream(
            model=get_anthropic_config().ANTHROPIC_MODEL,
            max_tokens=get_anthropic_config().ANTHROPIC_MAX_TOKEN,
            temperature=get_anthropic_config().ANTHROPIC_TEMPERATURE,
            top_k=get_anthropic_config().ANTHROPIC_TOP_K,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )

    async def _post_message_hooks(self, chat_session: ChatSession, user_content: str) -> None:
        count = await self.count_messages(chat_session.id)
        if count == 2 and chat_session.title is None:
            chat_session.title = await self.generate_title(user_content)
            await self._session.commit()
        if count % get_anthropic_config().SUMMARY_EVERY_N == 0:
            chat_session.summary = await self.generate_summary(chat_session.id)
            await self._session.commit()

    async def stream_response(self, session_id: UUID, user_content: str, user: User) -> AsyncGenerator[str, None]:
        chat_session = await self.get_session(session_id)
        self.check_session_owner(chat_session.user_id, user)
        await self.create_message(session_id, MessageRole.user, user_content)

        messages = await self.get_messages_for_anthropic(session_id, chat_session.summary)

        tool_was_called = False
        final_message = None

        try:
            async with self._get_stream(messages=messages) as stream:
                async for event in stream:
                    if event.type == "content_block_delta" and event.delta.type == "text_delta":
                        yield event.delta.text
                    elif event.type == "content_block_start" and event.content_block.type == "tool_use":
                        tool_was_called = True

                final_message = await stream.get_final_message()

        except Exception as error:
            yield f"[error: streaming failed]{error}"
            return

        if final_message:
            await self.create_message(
                chat_session.id, MessageRole.assistant,
                [ChatMessage.serialize_content_block(block) for block in final_message.content]
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
            await self.create_message(session_id, MessageRole.user, tool_result_content, is_tool=True)

            updated_messages = await self.get_messages_for_anthropic(session_id, chat_session.summary)

            try:
                async with self._get_stream(messages=updated_messages) as second_stream:
                    async for chunk in second_stream.text_stream:
                        yield chunk

                    final_message = await second_stream.get_final_message()
                if final_message:
                    await self.create_message(
                        chat_session.id, MessageRole.assistant,
                        [ChatMessage.serialize_content_block(block) for block in final_message.content]
                    )

            except Exception as error:
                yield f"[error: final streaming failed]{error}"
                return
