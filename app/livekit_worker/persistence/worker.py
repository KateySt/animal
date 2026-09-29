import asyncio
from contextlib import suppress
from typing import Any
from uuid import UUID

from app.core.logger import log
from app.db import MessageRole
from app.services.chat_session_service import ChatSessionService


class ConversationPersistenceWorker:
    def __init__(self, session_service: ChatSessionService, session_id: UUID) -> None:
        self._session_service = session_service
        self._session_id = session_id
        self._queue: asyncio.Queue[tuple[MessageRole, Any]] = asyncio.Queue(maxsize=256)
        self._consume_task = asyncio.create_task(self._consume(), name="persistence_consumer")

    def enqueue(self, row: tuple[MessageRole, Any]) -> None:
        try:
            self._queue.put_nowait(row)
        except asyncio.QueueFull:
            log.warning(f"persistence queue full for session {self._session_id}, dropping oldest item")
            self._queue.get_nowait()
            self._queue.task_done()
            self._queue.put_nowait(row)

    async def aclose(self) -> None:
        await self._queue.join()
        self._consume_task.cancel()
        with suppress(asyncio.CancelledError):
            await self._consume_task

    async def _consume(self) -> None:
        while True:
            role, content = await self._queue.get()
            persisted = await self._persist(role, content)
            if persisted and role == MessageRole.user:
                await self._run_post_message_hooks(content)
            self._queue.task_done()

    async def _persist(self, role: MessageRole, content: Any) -> bool:
        try:
            await self._session_service.create_message(self._session_id, role, content)
            return True
        except Exception:
            log.exception(f"Failed to persist LiveKit conversation item for session {self._session_id}")
            return False

    async def _run_post_message_hooks(self, content: Any) -> None:
        try:
            chat_session = await self._session_service.get_session(self._session_id)
            await self._session_service.run_post_message_hooks(chat_session, content)
        except Exception:
            log.exception(f"Failed to run post-message hooks for session {self._session_id}")
