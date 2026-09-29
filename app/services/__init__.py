from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.services.animal_service import AnimalService
from app.services.auth_service import AuthService
from app.services.chat_session_service import ChatSessionService
from app.services.health_log_service import HealthLogService
from app.services.image_service import ImageService
from app.services.invoice_service import InvoiceService
from app.services.minio_service import MinioService, minio_service
from app.services.permission_service import PermissionService
from app.services.redis_service import RedisService, redis_service
from app.services.refresh_token_service import RefreshTokenService
from app.services.resource_service import ResourceService
from app.services.role_service import RoleService
from app.services.user_service import UserService
from app.services.live_kit_service import create_live_kit_token


def get_health_log_service(session: AsyncSession = Depends(get_db_session)) -> HealthLogService:
    return HealthLogService(session)


def get_permission_service(session: AsyncSession = Depends(get_db_session)) -> PermissionService:
    return PermissionService(session)


def get_role_service(session: AsyncSession = Depends(get_db_session)) -> RoleService:
    return RoleService(session)


def get_refresh_token_service(session: AsyncSession = Depends(get_db_session)) -> RefreshTokenService:
    return RefreshTokenService(session)


def get_user_service(session: AsyncSession = Depends(get_db_session)) -> UserService:
    return UserService(session)


def get_animal_service(session: AsyncSession = Depends(get_db_session),
                       user_service: UserService = Depends(get_user_service)) -> AnimalService:
    return AnimalService(session, user_service)


def get_resource_service(session: AsyncSession = Depends(get_db_session)) -> ResourceService:
    return ResourceService(session)


def get_invoice_service(
    session: AsyncSession = Depends(get_db_session),
    user_service: UserService = Depends(get_user_service),
) -> InvoiceService:
    return InvoiceService(session, user_service)


def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
    refresh_token_service: RefreshTokenService = Depends(get_refresh_token_service),
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    return AuthService(session, refresh_token_service, user_service)


def get_chat_session_service(session: AsyncSession = Depends(get_db_session)) -> ChatSessionService:
    return ChatSessionService(session)


def get_image_service(
    session: AsyncSession = Depends(get_db_session),
    session_service: ChatSessionService = Depends(get_chat_session_service),
) -> ImageService:
    return ImageService(session, session_service)
