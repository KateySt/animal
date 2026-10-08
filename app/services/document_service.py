import re
import uuid
from collections.abc import Sequence
from pathlib import PurePath
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_book_rag_config
from app.core.book_rag import request_embedding
from app.core.error_codes import ErrorCode
from app.core.exceptions import BadRequestError, NotFoundError
from app.db import DocumentStatus
from app.db.models import ChatDocument
from app.db.models.user import User
from app.services.chat_session_service import ChatSessionService
from app.services.document_purger import document_purger
from app.services.minio_service import documents_storage

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


class DocumentService:
    def __init__(self, session: AsyncSession, chat_session_service: ChatSessionService) -> None:
        self.session = session
        self.chat_session_service = chat_session_service

    @staticmethod
    def _safe_object_filename(filename: str) -> str:
        # The original name stays in ChatDocument.filename; the object key only needs to be readable and safe
        name = _UNSAFE_FILENAME_CHARS.sub("_", PurePath(filename).name).strip("._")
        return name[:100] or "document"

    async def count_documents(self, chat_session_id: UUID) -> int:
        result = await self.session.execute(select(func.count()).where(ChatDocument.chat_session_id == chat_session_id))
        return result.scalar_one()

    async def get_document(self, document_id: UUID, chat_session_id: UUID | None = None) -> ChatDocument:
        query = select(ChatDocument).where(ChatDocument.id == document_id)
        if chat_session_id is not None:
            query = query.where(ChatDocument.chat_session_id == chat_session_id)
        result = await self.session.execute(query)
        document = result.scalar_one_or_none()

        if document is None:
            raise NotFoundError(ErrorCode.DOCUMENT_NOT_FOUND)
        return document

    async def delete_document(self, chat_session_id: UUID, document_id: UUID, user: User) -> None:
        chat_session = await self.chat_session_service.get_session(chat_session_id)
        self.chat_session_service.check_session_owner(chat_session.user_id, user)

        document = await self.get_document(document_id, chat_session_id)

        await document_purger.purge([document])
        await self.session.delete(document)
        await self.session.commit()

    async def set_status(self, document_id: UUID, status: DocumentStatus, error: str | None) -> ChatDocument:
        document = await self.get_document(document_id)
        document.status = status
        document.error_message = error
        await self.session.commit()
        return document

    async def list_documents(self, chat_session_id: UUID, user: User) -> Sequence[ChatDocument]:
        chat_session = await self.chat_session_service.get_session(chat_session_id)
        self.chat_session_service.check_session_owner(chat_session.user_id, user)
        result = await self.session.execute(
            select(ChatDocument).where(ChatDocument.chat_session_id == chat_session_id).order_by(
                ChatDocument.created_at)
        )
        return result.scalars().all()

    async def upload_document(self, chat_session_id: UUID, user: User, file: UploadFile) -> ChatDocument:
        chat_session = await self.chat_session_service.get_session(chat_session_id)
        self.chat_session_service.check_session_owner(chat_session.user_id, user)

        filename = file.filename
        content_type = file.content_type
        data = await file.read()

        config = get_book_rag_config()
        existing_count = await self.count_documents(chat_session_id)
        if existing_count >= config.BOOK_RAG_MAX_DOCUMENTS_PER_SESSION:
            raise BadRequestError(ErrorCode.DOCUMENT_LIMIT_REACHED)

        object_name = f"chat-documents/{chat_session_id}/{uuid.uuid4().hex}_{self._safe_object_filename(filename)}"
        await documents_storage.upload_file(object_name, data, content_type)

        document = ChatDocument(
            chat_session_id=chat_session_id,
            filename=filename,
            content_type=content_type,
            size_bytes=len(data),
            minio_object_name=object_name,
            status=DocumentStatus.embedding,
        )
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)

        try:
            await request_embedding(chat_session_id, document.id, filename, object_name)
        except Exception:
            document.failed()
            await self.session.commit()

        return document
