from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import UnauthorizedError
from app.core.config import get_auth_config
from app.core.security import (
    generate_refresh_token,
    hash_refresh_token,
)
from app.db.models import refresh_token_crud
from app.schemas.user import RefreshTokenCreate, RefreshTokenInternal


class RefreshTokenService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, refresh_token: str) -> RefreshTokenInternal:
        token = await refresh_token_crud.get(
            self._session,
            schema_to_select=RefreshTokenInternal,
            return_as_model=True,
            token_hash=hash_refresh_token(refresh_token),
        )
        if token is None:
            raise UnauthorizedError("Invalid refresh token")
        return token

    async def create(self, user_id: UUID) -> tuple[str, RefreshTokenInternal]:
        generated_refresh_token = generate_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(days=get_auth_config().REFRESH_TOKEN_TIME_DAYS)
        new_token = await refresh_token_crud.create(
            self._session,
            RefreshTokenCreate(
                user_id=user_id,
                token_hash=hash_refresh_token(generated_refresh_token),
                expires_at=expires_at,
            ),
            schema_to_select=RefreshTokenInternal,
            return_as_model=True,
        )
        return generated_refresh_token, new_token

    async def rotate(self, old_token: RefreshTokenInternal) -> tuple[str, RefreshTokenInternal]:
        generated_refresh_token, new_token = await self.create(old_token.user_id)
        await refresh_token_crud.update(
            self._session,
            {"is_revoked": True, "rotated_to": new_token.id},
            id=old_token.id,
        )
        return generated_refresh_token, new_token

    async def revoke(self, refresh_token: str) -> None:
        await refresh_token_crud.update(
            self._session,
            {"is_revoked": True},
            token_hash=hash_refresh_token(refresh_token),
        )

    async def revoke_family(self, refresh_token: RefreshTokenInternal) -> None:
        if refresh_token.is_revoked:
            await refresh_token_crud.update(
                self._session,
                {"is_revoked": True},
                allow_multiple=True,
                user_id=refresh_token.user_id,
            )
            raise UnauthorizedError("Refresh token reuse detected, all sessions revoked")
