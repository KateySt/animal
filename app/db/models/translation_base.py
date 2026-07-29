from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.db.enums import Locale
from app.db.mixins import IDMixin
from app.db.models.base import Base


class TranslationBase(Base, IDMixin):
    __abstract__ = True

    locale: Mapped[Locale] = mapped_column(Enum(Locale), nullable=False)

    @declared_attr
    def parent_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            UUID(as_uuid=True),
            ForeignKey(f"{cls.__parent_table__}.id", ondelete="CASCADE"),
            nullable=False,
        )

    @declared_attr
    def parent(cls):
        parent_class = cls.__name__.replace("Translation", "")
        return relationship(parent_class, back_populates="translations")

    @declared_attr
    def __table_args__(cls):
        return (UniqueConstraint("parent_id", "locale", name=f"uq_{cls.__parent_table__}_translation_locale"),)
