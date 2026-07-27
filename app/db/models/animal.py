from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Gender, IDMixin, TimestampMixin
from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.health_log import HealthLog


class Animal(Base, IDMixin, TimestampMixin):
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    caretaker_notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), default=Gender.male, nullable=False)
    birth_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    owner: Mapped["User"] = relationship("User", back_populates="animals")
    health_logs: Mapped[list["HealthLog"]] = relationship(
        "HealthLog",
        back_populates="animal",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
