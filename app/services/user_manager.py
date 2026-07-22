import uuid

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import auth_config
from app.db.models.oauth_account import OAuthAccount
from app.db.models.user import User
from app.db.session import get_db_session


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = auth_config.RESET_PASSWORD_TOKEN_SECRET
    verification_token_secret = auth_config.VERIFICATION_TOKEN_SECRET

    async def on_after_register(self, user: User, request: Request | None = None):
        print(f"User {user.email} has registered.")

    async def on_after_forgot_password(self, user: User, token: str, request: Request | None = None):
        print(f"User {user.email} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(self, user: User, token: str, request: Request | None = None):
        print(f"Verification requested for user {user.email}. Verification token: {token}")


async def get_user_db(session: AsyncSession = Depends(get_db_session)):
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    return JWTStrategy(
        secret=auth_config.ACCESS_TOKEN_SECRET,
        lifetime_seconds=auth_config.ACCESS_TOKEN_TIME_MINUTES * 60,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=BearerTransport(tokenUrl="auth/jwt/login"),
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
