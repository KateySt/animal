from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import IDMixin, TimestampMixin
from app.db.mixins import TranslatableMixin
from app.db.models.base import Base
from app.db.models.invoice import invoice_health_log_association
from app.db.models.translation_base import TranslationBase

if TYPE_CHECKING:
    from app.db.models.animal import Animal
    from app.db.models.invoice import Invoice


class HealthLog(Base, IDMixin, TimestampMixin, TranslatableMixin):
    animal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("animals.id", ondelete="CASCADE"), nullable=False)

    animal: Mapped[Animal] = relationship("Animal", back_populates="health_logs")
    invoices: Mapped[list[Invoice]] = relationship(
        "Invoice",
        secondary=invoice_health_log_association,
        back_populates="health_logs",
    )


class HealthLogTranslation(TranslationBase):
    __tablename__ = "healthlogtranslations"
    __parent_table__ = "healthlogs"

    procedure_name: Mapped[str] = mapped_column(String(100), nullable=False)
    examination_findings: Mapped[str | None] = mapped_column(String(255), nullable=True)
