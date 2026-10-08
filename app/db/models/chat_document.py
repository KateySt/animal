from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import DocumentStatus
from app.db.mixins import IDMixin, TimestampMixin
from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.chat_session import ChatSession


class ChatDocument(Base, IDMixin, TimestampMixin):
    chat_session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chatsessions.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(SAEnum(DocumentStatus, name="documentstatus"), nullable=False, default=DocumentStatus.uploading)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    chat_session: Mapped[ChatSession] = relationship("ChatSession", back_populates="documents", lazy="noload")

    def failed(self):
        self.status = DocumentStatus.failed
        self.error_message = "Document search service is unavailable"

