import uuid
from collections.abc import Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db import TokenType
from app.db.models.permission import Permission
from app.db.models.role import Role
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas import Principal
from app.services import redis_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login", auto_error=False)


async def get_current_principal(
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> Principal:
    if token is None:
        raise UnauthorizedError("Not authenticated", headers={"WWW-Authenticate": "Bearer"})

    payload = decode_access_token(token)
    if payload is None or payload.get("type") != TokenType.access:
        raise UnauthorizedError("Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})

    user_id = uuid.UUID(payload.get("sub"))
    token_permissions_version: int = payload.get("permissions_version", 0)
    cached_permissions_version = await redis_service.get_cache(f"permissions_version:{user_id}")

    if cached_permissions_version is None:
        result = await session.execute(select(User.permissions_version).where(User.id == user_id))
        current_permissions_version = result.scalar_one_or_none()
        if current_permissions_version is None:
            raise UnauthorizedError("User not found", headers={"WWW-Authenticate": "Bearer"})
        await redis_service.set_cache(f"permissions_version:{user_id}", current_permissions_version, ttl=3600)
    else:
        current_permissions_version = int(cached_permissions_version)

    if token_permissions_version < current_permissions_version:
        raise UnauthorizedError("Token invalidated, please refresh", headers={"WWW-Authenticate": "Bearer"})

    return Principal(
        user_id=user_id,
        is_superuser=bool(payload.get("is_superuser", False)),
        scopes=payload.get("scopes", []),
    )


def require_scopes(*scopes: str) -> Callable:
    async def _check(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.is_superuser:
            return principal
        for scope in scopes:
            if scope not in principal.scopes:
                raise ForbiddenError(f"Missing scope: {scope}")
        return principal

    return _check


def require_roles(*role_names: str) -> Callable:
    async def _check(
        principal: Principal = Depends(get_current_principal),
        user: User = Depends(get_current_user),
    ) -> Principal:
        if principal.is_superuser:
            return principal
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        user_role_names = {role.name for role in user.roles}
        if not user_role_names.intersection(role_names):
            raise ForbiddenError(f"Required role(s): {', '.join(role_names)}")
        return principal

    return _check


async def require_superuser(principal: Principal = Depends(get_current_principal)) -> Principal:
    if not principal.is_superuser:
        raise ForbiddenError("Superuser access required")
    return principal


async def get_current_user(
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    result = await session.execute(
        select(User)
        .where(User.id == principal.user_id)
        .options(
            selectinload(User.roles).selectinload(Role.permissions).selectinload(Permission.resource),
        )
    )
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user
