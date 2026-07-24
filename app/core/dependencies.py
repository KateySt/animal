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
    token_pv: int = payload.get("pv", 0)
    cached_pv = await redis_service.get_cache(f"pv:{user_id}")

    if cached_pv is None:
        result = await session.execute(select(User.permissions_version).where(User.id == user_id))
        current_pv = result.scalar_one_or_none()
        if current_pv is None:
            raise UnauthorizedError("User not found", headers={"WWW-Authenticate": "Bearer"})
        await redis_service.set_cache(f"pv:{user_id}", current_pv, ttl=3600)
    else:
        current_pv = int(cached_pv)

    if token_pv < current_pv:
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
