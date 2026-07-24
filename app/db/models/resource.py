from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.mixins import IDMixin, TimestampMixin
from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.permission import Permission


class Resource(Base, IDMixin, TimestampMixin):
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    permissions: Mapped[list[Permission]] = relationship(back_populates="resource", lazy="noload")
