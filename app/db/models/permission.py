from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.mixins import IDMixin, TimestampMixin
from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.resource import Resource
    from app.db.models.role import Role


class Permission(Base, IDMixin, TimestampMixin):
    __table_args__ = (UniqueConstraint("resource_id", "action", name="uq_permission_resource_action"),)

    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="RESTRICT"),
        index=True,
        nullable=False
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)

    resource: Mapped[Resource] = relationship(back_populates="permissions", lazy="selectin")
    roles: Mapped[list[Role]] = relationship(secondary="role_permissions", lazy="noload", back_populates="permissions")

    @property
    def scope(self) -> str:
        return f"{self.resource.name}:{self.action}"
