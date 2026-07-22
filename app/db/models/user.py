from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.mixins import IDMixin, TimestampMixin
from app.db.models.base import Base


class User(Base, IDMixin, TimestampMixin):
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
