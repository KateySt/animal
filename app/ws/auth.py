import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db import TokenType
from app.db.models.user import User
from app.schemas import Principal
from app.services.redis_service import redis_service


async def get_current_principal_ws(token: str, session: AsyncSession) -> Principal:
    payload = decode_access_token(token)
    if payload is None or payload.get("type") != TokenType.access:
        raise UnauthorizedError(ErrorCode.INVALID_TOKEN)

    user_id = uuid.UUID(payload.get("sub"))
    token_permissions_version: int = payload.get("permissions_version", 0)
    cached_permissions_version = await redis_service.get_cache(f"permissions_version:{user_id}")

    if cached_permissions_version is None:
        result = await session.execute(select(User.permissions_version).where(User.id == user_id))
        current_permissions_version = result.scalar_one_or_none()
        if current_permissions_version is None:
            raise UnauthorizedError(ErrorCode.USER_NOT_FOUND)
        await redis_service.set_cache(f"permissions_version:{user_id}", current_permissions_version, ttl=3600)
    else:
        current_permissions_version = int(cached_permissions_version)

    if token_permissions_version < current_permissions_version:
        raise UnauthorizedError(ErrorCode.TOKEN_INVALIDATED)

    return Principal(
        user_id=user_id,
        is_superuser=bool(payload.get("is_superuser", False)),
        scopes=payload.get("scopes", []),
    )
