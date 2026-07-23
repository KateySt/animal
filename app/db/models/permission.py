from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.enums import Policy, Role
from app.db.mixins import IDMixin, TimestampMixin
from app.db.models.base import Base


class Permission(Base, IDMixin, TimestampMixin):
    role: Mapped[Role] = mapped_column(Enum(Role, name="role"), nullable=False)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[Policy] = mapped_column(Enum(Policy, name="policy"), nullable=False)
