from collections.abc import Sequence
from uuid import UUID

import httpx
import urllib3.exceptions
from minio.error import S3Error
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.book_rag import delete_documents as book_rag_delete_documents
from app.core.exceptions import BookRagUnavailableError, DocumentStorageUnavailableError
from app.db.models import ChatDocument, ChatSession
from app.services.minio_service import MinioService, ObjectDeletionError, documents_storage


class DocumentPurger:
    def __init__(self, storage: MinioService) -> None:
        self._storage = storage

    async def purge(self, documents: Sequence[ChatDocument]) -> None:
        if not documents:
            return
        try:
            await book_rag_delete_documents([document.id for document in documents])
        except httpx.HTTPError as error:
            raise BookRagUnavailableError(detail=str(error)) from error
        try:
            await self._storage.delete_files([document.minio_object_name for document in documents])
        except (ObjectDeletionError, S3Error, urllib3.exceptions.HTTPError) as error:
            raise DocumentStorageUnavailableError(detail=str(error)) from error

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
