from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.mixins import IDMixin, TimestampMixin
from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.chat_message import ChatMessage
    from app.db.models.user import User


class ChatSession(Base, IDMixin, TimestampMixin):
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)
    last_summarized_message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    messages: Mapped[list[ChatMessage]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="noload",
        order_by="ChatMessage.created_at",
    )
    user: Mapped[User] = relationship("User", back_populates="chat_sessions", lazy="noload")
