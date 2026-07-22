from datetime import UTC, datetime

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsError, NotFoundError, UnauthorizedError
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.db import TokenType
from app.db.models import user_crud
from app.schemas import TokenResponse, UserInternalCreate, UserLogin, UserRegister, UserResponse, UserWithPassword
from app.services import RedisService


class UserService:
    def __init__(self, session: AsyncSession, redis: RedisService) -> None:
        self._session = session
        self._redis = redis

    async def get_by_email(self, email: EmailStr) -> UserResponse:
        user = await user_crud.get(self._session, schema_to_select=UserResponse, return_as_model=True, email=email)
        if user is None:
            raise NotFoundError(f"User {email} not found")
        return user

    async def register(self, payload: UserRegister) -> UserResponse:
        existing = await user_crud.get(self._session, schema_to_select=UserResponse, return_as_model=True, email=payload.email)
        if existing:
            raise AlreadyExistsError("User with this email already exists")
        internal = UserInternalCreate(
            name=payload.name,
            email=payload.email,
            hashed_password=hash_password(payload.password),
        )
        created = await user_crud.create(self._session, internal, return_as_model=True, schema_to_select=UserResponse)
        return created

    async def login(self, payload: UserLogin) -> TokenResponse:
        user = await user_crud.get(self._session, schema_to_select=UserWithPassword, return_as_model=True, email=payload.email)

        if user is None:
            raise NotFoundError("Invalid credentials")
        if not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedError("Invalid credentials")

        return TokenResponse(
            access_token=create_access_token(user.email),
            refresh_token=create_refresh_token(user.email),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != TokenType.refresh:
            raise UnauthorizedError("Invalid token type")

        jti = payload.get("jti")
        if not jti:
            raise UnauthorizedError("Invalid token")

        if await self._redis.get_cache(f"rt:used:{jti}"):
            raise UnauthorizedError("Refresh token already used")

        exp = payload.get("exp")
        ttl = int(exp - datetime.now(UTC).timestamp())
        if ttl <= 0:
            raise UnauthorizedError("Refresh token expired")

        await self._redis.set_cache(f"rt:used:{jti}", 1, ttl=ttl)
        user = await self.get_by_email(payload.get("sub"))

        return TokenResponse(
            access_token=create_access_token(user.email),
            refresh_token=create_refresh_token(user.email),
        )
