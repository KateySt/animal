from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.enums import Role
from app.db.mixins import TimestampMixin
from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.oauth_account import OAuthAccount


class User(SQLAlchemyBaseUserTableUUID, Base, TimestampMixin):
    role: Mapped[Role] = mapped_column(Enum(Role, name="role"), default=Role.user, server_default=Role.user, nullable=False)
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship("OAuthAccount", lazy="joined")
