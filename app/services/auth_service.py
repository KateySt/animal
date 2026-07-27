import secrets
from datetime import UTC, datetime

from authlib.common.security import generate_token
from authlib.jose import jwt as authlib_jwt
from authlib.oidc.core import CodeIDToken
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import BadRequestError
from app.core.config import get_auth_config
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    verify_password,
)
from app.schemas.auth import Auth2Redirect, IssuedTokens
from app.schemas.user import UserInternal
from app.services.google_oauth_service import google_oauth_service
from app.services.redis_service import redis_service
from app.services.refresh_token_service import RefreshTokenService
from app.services.user_service import UserService


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        refresh_token_service: RefreshTokenService,
        user_service: UserService,
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

    async def _issue_tokens(self, user: UserInternal) -> IssuedTokens:
        generated_refresh_token, new_refresh_token = await self._refresh_token_service.create(user.id)
        scopes = await self._user_service.get_scopes(user.id)
        await redis_service.set_cache(f"permissions_version:{user.id}", user.permissions_version, ttl=3600)
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

    @staticmethod
    async def get_authorize_url() -> Auth2Redirect:
        state = secrets.token_urlsafe(32)
        nonce = generate_token()
        url, _ = google_oauth_service.client.create_authorization_url(
            google_oauth_service.metadata["authorization_endpoint"],
            redirect_uri=get_auth_config().GOOGLE_REDIRECT_URI,
            state=state,
            nonce=nonce,
        )
        return Auth2Redirect(authorization_url=url)

    async def google_callback(self, code: str, state: str) -> IssuedTokens:
        async with google_oauth_service.client as client:
            token = await client.fetch_token(
                google_oauth_service.metadata["token_endpoint"],
                code=code,
                redirect_uri=get_auth_config().GOOGLE_REDIRECT_URI,
            )

        claims = await authlib_jwt.decode(
            token["id_token"],
            google_oauth_service.jwks,
            claims_cls=CodeIDToken,
            claims_options={
                "iss": {"essential": True, "value": "https://accounts.google.com"},
                "aud": {"essential": True, "value": get_auth_config().GOOGLE_CLIENT_ID},
                "nonce": {"essential": True, "value": state},
            },
        )
        claims.validate()

        account_email = claims.get("email")
        if not account_email or not claims.get("email_verified"):
            raise BadRequestError("Google account has problem with email")

        user = await self._user_service.get_by_oauth("google", claims["sub"])
        if user is None:
            user = await self._user_service.get_by_email_or_create_with_oauth(account_email, claims["sub"])
        self._user_service.check_active(user)
        return await self._issue_tokens(user)
