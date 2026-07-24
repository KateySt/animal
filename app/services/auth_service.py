from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    verify_password,
)
from app.schemas.auth import IssuedTokens
from app.schemas.user import UserInternal
from app.services.redis_service import redis_service
from app.services.refresh_token_service import RefreshTokenService
from app.services.user_service import UserSrvice


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        refresh_token_service: RefreshTokenService,
        user_service: UserSrvice,
    ) -> None:
        self._session = session
        self._refresh_token_service = refresh_token_service
        self._user_service = user_service

    async def register(self, email: str, password: str) -> UserInternal:
        return await self._user_service.create(email, password)

    async def login(self, email: str, password: str) -> IssuedTokens:
        user = await self._user_service.get_by_email(email)
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        self._user_service.check_active(user)
        return await self._issue_tokens(user)

    async def _issue_tokens(self, user) -> IssuedTokens:
        generated_refresh_token, new_refresh_token = await self._refresh_token_service.create(user.id)
        scopes = await self._user_service.get_scopes(user.id)

        await redis_service.set_cache(f"pv:{user.id}", user.permissions_version, ttl=3600)
        return IssuedTokens(
            access_token=create_access_token(user, scopes=list(scopes)),
            refresh_token=generated_refresh_token,
            refresh_expires_at=new_refresh_token.expires_at,
        )

    async def refresh(self, raw_refresh: str) -> IssuedTokens:
        refresh_token = await self._refresh_token_service.get(raw_refresh)

        if refresh_token.expires_at < datetime.now(UTC):
            raise UnauthorizedError("Refresh token expired")

        await self._refresh_token_service.revoke_family(refresh_token)

        user = await self._user_service.get_by_id(refresh_token.user_id)
        self._user_service.check_active(user)
        scopes = await self._user_service.get_scopes(user.id)
        generated_refresh_token, new_refresh_token = await self._refresh_token_service.rotate(refresh_token)
        return IssuedTokens(
            access_token=create_access_token(user, scopes=list(scopes)),
            refresh_token=generated_refresh_token,
            refresh_expires_at=new_refresh_token.expires_at,
        )

    async def logout(self, raw_refresh: str) -> None:
        await self._refresh_token_service.revoke(raw_refresh)

    async def google_callback(self, account_id: str, account_email: str, access_token: str,
                              expires_at: int | None) -> IssuedTokens:
        user = await self._user_service.get_by_oauth("google", account_id)
        if user is None:
            user = await self._user_service.get_by_email_or_create_with_oauth(account_email, access_token, expires_at,
                                                                              account_id)
        self._user_service.check_active(user)
        return await self._issue_tokens(user)
