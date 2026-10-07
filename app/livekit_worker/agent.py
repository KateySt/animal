from uuid import UUID

from livekit.agents import Agent, llm
from livekit.agents.voice.generation import update_instructions
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.prompts import CHAT_DOCUMENTS_TEMPLATE, SYSTEM_PROMPT
from app.services.ai_service import get_document_statuses


class ChatAgent(Agent):
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        chat_session_id: UUID,
        **kwargs,
    ) -> None:
        super().__init__(instructions=SYSTEM_PROMPT, **kwargs)
        self._session_factory = session_factory
        self._chat_session_id = chat_session_id

    async def refresh_documents(self, turn_ctx: llm.ChatContext | None = None) -> None:
        instructions = await self._build_instructions()
        if instructions != self.instructions:
            await self.update_instructions(instructions)
        if turn_ctx is not None:
            update_instructions(turn_ctx, instructions=instructions, add_if_missing=True)

    async def on_user_turn_completed(self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage) -> None:
        await self.refresh_documents(turn_ctx)

    async def _build_instructions(self) -> str:
        async with self._session_factory() as session:
            statuses = await get_document_statuses(session, self._chat_session_id)
        documents = CHAT_DOCUMENTS_TEMPLATE.format(
            ready=", ".join(statuses["ready_documents"]) or "none",
            processing=", ".join(statuses["processing_documents"]) or "none",
            failed=", ".join(statuses["failed_documents"]) or "none",
        )
        return f"{SYSTEM_PROMPT}\n\n{documents}"
