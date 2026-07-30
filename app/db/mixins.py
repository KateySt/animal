import uuid
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.db.enums import Locale


class IDMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TranslatableMixin:
    @declared_attr
    def translations(cls) -> Mapped[list[Any]]:
        return relationship(
            f"{cls.__name__}Translation",
            back_populates="parent",
            cascade="all, delete-orphan",
            lazy="selectin",
        )

    def get_translation(self, locale: str) -> object | None:
        for translation in self.translations:
            if translation.locale == locale:
                return translation
        for translation in self.translations:
            if translation.locale == Locale.en:
                return translation
        return None
