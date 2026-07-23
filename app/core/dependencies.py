from collections.abc import Callable

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError
from app.core.fastapi_users_setup import current_active_user
from app.db import get_db_session
from app.db.enums import Policy, Role
from app.db.models import permission_crud
from app.db.models.user import User


async def _has_permission(session: AsyncSession, role: Role, resource: str, action: Policy) -> bool:
    permission = await permission_crud.get(session, role=role, resource=resource, action=action)
    return permission is not None


def require_permission(resource: str, policy: Policy) -> Callable:
    async def dependency(
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_db_session),
    ) -> User:
        if user.is_superuser:
            return user

        allowed = await _has_permission(session, user.role, resource, policy)
        if not allowed:
            raise ForbiddenError("Insufficient permissions")

        return user

    return dependency


def require_superuser(user: User = Depends(current_active_user)) -> User:
    if not user.is_superuser:
        raise ForbiddenError("Superuser access required")
    return user
