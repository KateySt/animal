import asyncio
from contextlib import suppress
from uuid import UUID

from livekit.agents import Agent
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.logger import log
from app.db import DocumentStatus
from app.db.models import ChatDocument
from app.livekit_worker.tools import build_search_documents_function_tool

POLL_INTERVAL_SECONDS = 5.0


class DocumentToolWatcher:
    def __init__(self, agent: Agent, session_factory: async_sessionmaker[AsyncSession], session_id: UUID) -> None:
        self._agent = agent
        self._session_factory = session_factory
        self._session_id = session_id
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._watch(), name="document_tool_watcher")

    async def aclose(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task

    async def _watch(self) -> None:
        async with self._session_factory() as session:
            while True:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                try:
                    ready_count = await self._count_ready_documents(session)
                except Exception:
                    log.exception(f"document_tool_watcher: failed to poll documents for session {self._session_id}")
                    continue
                if ready_count > 0:
                    await self._agent.update_tools([*self._agent.tools, build_search_documents_function_tool(self._session_id)])
                    return

    async def _count_ready_documents(self, session: AsyncSession) -> int:
        result = await session.execute(
            select(func.count())
            .select_from(ChatDocument)
            .where(ChatDocument.chat_session_id == self._session_id)
            .where(ChatDocument.status == DocumentStatus.ready)
        )
        return result.scalar_one()
