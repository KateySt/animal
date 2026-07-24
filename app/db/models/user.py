from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.mixins import IDMixin, TimestampMixin
from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.oauth_account import OAuthAccount
    from app.db.models.refresh_token import RefreshToken
    from app.db.models.role import Role


class User(Base, IDMixin, TimestampMixin):
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    permissions_version: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)

    roles: Mapped[list[Role]] = relationship(secondary="user_roles", lazy="selectin", back_populates="users")
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(lazy="selectin", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(lazy="noload", cascade="all, delete-orphan")
