import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.mixins import IDMixin, TimestampMixin
from app.db.models.base import Base


class OAuthAccount(Base, IDMixin, TimestampMixin):
    __table_args__ = (UniqueConstraint("oauth_name", "account_id", name="uq_oauth_provider_account"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    oauth_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    account_id: Mapped[str] = mapped_column(String(320), index=True, nullable=False)
    account_email: Mapped[str] = mapped_column(String(320), nullable=False)
