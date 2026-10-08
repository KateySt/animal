from collections.abc import Sequence
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.blob import BlobStorage, documents_storage
from app.core.book_rag import delete_documents as book_rag_delete_documents
from app.core.exceptions import BookRagUnavailableError
from app.db.models import ChatDocument, ChatSession


class DocumentPurger:
    def __init__(self, storage: BlobStorage) -> None:
        self._storage = storage

    async def purge(self, documents: Sequence[ChatDocument]) -> None:
        if not documents:
            return
        try:
            await book_rag_delete_documents([document.id for document in documents])
        except httpx.HTTPError as error:
            raise BookRagUnavailableError(detail=str(error)) from error
        await self._storage.delete_files([document.storage_key for document in documents])

    async def purge_sessions(self, session: AsyncSession, chat_session_ids: Sequence[UUID]) -> None:
        result = await session.execute(select(ChatDocument).where(ChatDocument.chat_session_id.in_(chat_session_ids)))
        await self.purge(result.scalars().all())

    async def purge_user(self, session: AsyncSession, user_id: UUID) -> None:
        result = await session.execute(
            select(ChatDocument).join(ChatSession, ChatDocument.chat_session_id == ChatSession.id)
            .where(ChatSession.user_id == user_id)
        )
        await self.purge(result.scalars().all())


document_purger = DocumentPurger(documents_storage)
