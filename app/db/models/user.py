from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import Mapped, relationship

from app.db.mixins import TimestampMixin
from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.oauth_account import OAuthAccount


class User(SQLAlchemyBaseUserTableUUID, Base, TimestampMixin):
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship("OAuthAccount", lazy="joined")
