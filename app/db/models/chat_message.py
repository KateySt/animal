from __future__ import annotations

import uuid
from typing import Any
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import MessageRole
from app.db.mixins import IDMixin, TimestampMixin
from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.chat_session import ChatSession


class ChatMessage(Base, IDMixin, TimestampMixin):
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chatsessions.id", ondelete="CASCADE"),
                                                  nullable=False, index=True)
    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole, name="messagerole"), nullable=False)
    content: Mapped[Any] = mapped_column(JSON, nullable=False)
    is_tool: Mapped[bool] = mapped_column(Boolean, nullable=False)

    session: Mapped[ChatSession] = relationship("ChatSession", back_populates="messages", lazy="noload")

    @staticmethod
    def serialize_content_block(block) -> dict:
        if block.type == "text":
            return {"type": "text", "text": block.text}
        if block.type == "tool_use":
            return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
        return {"type": block.type}
