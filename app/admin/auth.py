from fastapi_users.db import SQLAlchemyUserDatabase
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError

from app.db.models.oauth_account import OAuthAccount
from app.db.models.user import User
from app.db.session import AsyncSessionLocal
from app.services.user_manager import UserManager


class AdminAuthProvider(AuthProvider):
    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        async with AsyncSessionLocal() as session:
            user_db = SQLAlchemyUserDatabase(session, User, OAuthAccount)
            manager = UserManager(user_db)
            credentials = type("Credentials", (), {"username": username, "password": password})()
            user = await manager.authenticate(credentials)
            if user is None or not user.is_active or not user.is_superuser:
                raise FormValidationError({"password": "Invalid credentials"})

        request.session.update({"admin_username": user.email, "admin_name": user.email})
        return response

    async def is_authenticated(self, request: Request) -> bool:
        return bool(request.session.get("admin_username"))

    def get_admin_config(self, request: Request) -> AdminConfig:
        return AdminConfig(app_title="Animal")

    def get_admin_user(self, request: Request) -> AdminUser:
        return AdminUser(username=request.session.get("admin_name", ""))

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response
