from collections.abc import AsyncGenerator
from uuid import UUID

import ai
from ai.ui.ai_sdk import outbound_stream as ui_stream
from ai.ui.ai_sdk import ui_events
from app.core.anthropic import (
    from_ai_message,
    generate_summary,
    generate_title,
    get_model,
    inference_params,
    serialize_transcript,
    to_ai_messages,
)
from app.core.config import get_anthropic_config
from app.core.logger import log
from app.core.prompts import SYSTEM_PROMPT
from app.core.tools.definitions import build_get_invoices_tool
from app.db import MessageRole
from app.db.models import ChatSession
from app.db.models.user import User
from app.services.chat_session_service import ChatSessionService
from sqlalchemy.ext.asyncio import AsyncSession


class AnthropicChatService:
    def __init__(self, session: AsyncSession, session_service: ChatSessionService) -> None:
        self._session = session
        self._session_service = session_service

    async def _post_message_hooks(self, chat_session: ChatSession, user_content: str) -> None:
        if chat_session.title is None:
            chat_session.title = await generate_title(user_content)
            await self._session.commit()

        user_count = await self._session_service.count_user_messages(chat_session.id)
        if user_count % get_anthropic_config().SUMMARY_EVERY_N == 0:
            new_rows = await self._session_service.get_messages_since_summary(
                chat_session.id,
                chat_session.last_summarized_message_id
            )
            if new_rows:
                summary = await generate_summary(chat_session.summary, serialize_transcript(new_rows))
                last_id = await self._session_service.get_last_message_id(chat_session.id)
                await self._session_service.set_summary(chat_session, summary, last_id)

    async def stream_response(self, session_id: UUID, user_content: str, user: User) -> AsyncGenerator[str, None]:
        chat_session = await self._session_service.get_session(session_id)
        self._session_service.check_session_owner(chat_session.user_id, user)
        await self._session_service.create_message(session_id, MessageRole.user, user_content)

        try:
            rows = await self._session_service.get_messages_for_anthropic(session_id)
            messages = [ai.system_message(SYSTEM_PROMPT), *to_ai_messages(rows, chat_session.summary)]
            initial_count = len(messages)

            agent = ai.Agent(tools=[build_get_invoices_tool(self._session, user)])

            async with agent.run(
                    get_model(), messages, params=inference_params(get_anthropic_config().ANTHROPIC_MAX_TOKEN)
            ) as stream:
                async for chunk in ai.ui.ai_sdk.to_sse(stream):
                    yield chunk

                for message in stream.messages[initial_count:]:
                    await self._session_service.create_message(
                        chat_session.id,
                        MessageRole.tool if message.role == "tool" else MessageRole.assistant,
                        from_ai_message(message),
                    )
        except Exception:
            yield ui_stream.format_sse(ui_events.UIErrorEvent(error_text="Streaming failed"))
            yield ui_stream.format_done_sse()
            return

        await self._post_message_hooks(chat_session, user_content)
