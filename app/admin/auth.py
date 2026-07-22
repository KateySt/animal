from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError

from app.core.exceptions import CustomError
from app.db.session import AsyncSessionLocal
from app.schemas import UserLogin
from app.services.user_service import UserService


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
            service = UserService(session)
            try:
                await service.login(UserLogin(email=username, password=password))
            except CustomError as error:
                raise FormValidationError({"password": error.detail})
            user = await service.get_by_email(username)

        request.session.update({"admin_username": user.email, "admin_name": user.name})
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
