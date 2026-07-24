from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import IDMixin, TimestampMixin
from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.animal import Animal


class HealthLog(Base, IDMixin, TimestampMixin):
    animal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("animals.id", ondelete="CASCADE"), nullable=False)
    procedure_name: Mapped[str] = mapped_column(String(100), nullable=False)
    examination_findings: Mapped[str | None] = mapped_column(String(255), nullable=True)

    animal: Mapped[Animal] = relationship("Animal", back_populates="health_logs")
