from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, Enum, ForeignKey, Integer, Table, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import IDMixin, InvoiceStatus, TimestampMixin
from app.db.enums import Currency
from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.animal import Animal
    from app.db.models.health_log import HealthLog
    from app.db.models.user import User

invoice_health_log_association = Table(
    "invoice_health_logs",
    Base.metadata,
    Column("invoice_id", UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), primary_key=True),
    Column("health_log_id", UUID(as_uuid=True), ForeignKey("healthlogs.id", ondelete="CASCADE"), primary_key=True),
)

_CENTS_PER_UNIT: dict[Currency, int] = {
    Currency.usd: 100,
    Currency.uah: 100,
}


class Invoice(Base, IDMixin, TimestampMixin):
    animal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("animals.id", ondelete="CASCADE"), nullable=False)
    amount_in_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.pending)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), default=Currency.usd)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)

    user: Mapped[User] = relationship("User", back_populates="invoices")
    animal: Mapped[Animal] = relationship("Animal")
    health_logs: Mapped[list[HealthLog]] = relationship("HealthLog", secondary=invoice_health_log_association, back_populates="invoices")

    def to_float(self, currency: Currency = Currency.usd) -> float:
        return self.amount_in_cents / _CENTS_PER_UNIT[currency]

    @classmethod
    def from_float(cls, amount: float, currency: Currency = Currency.usd) -> int:
        return round(amount * _CENTS_PER_UNIT[currency])
