from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.mixins import IDMixin, TimestampMixin
from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.permission import Permission
    from app.db.models.user import User


class Role(Base, IDMixin, TimestampMixin):
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    permissions: Mapped[list[Permission]] = relationship(secondary="role_permissions", lazy="selectin", back_populates="roles")
    users: Mapped[list[User]] = relationship(secondary="user_roles", lazy="noload", back_populates="roles")
