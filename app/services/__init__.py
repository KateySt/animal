from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.services.animal_service import AnimalService
from app.services.auth_service import AuthService
from app.services.health_log_service import HealthLogService
from app.services.permission_service import PermissionService
from app.services.redis_service import RedisService, redis_service
from app.services.refresh_token_service import RefreshTokenService
from app.services.resource_service import ResourceService
from app.services.role_service import RoleService
from app.services.user_service import UserSrvice


def get_animal_service(session: AsyncSession = Depends(get_db_session)) -> AnimalService:
    return AnimalService(session)


def get_health_log_service(session: AsyncSession = Depends(get_db_session)) -> HealthLogService:
    return HealthLogService(session)


def get_permission_service(session: AsyncSession = Depends(get_db_session)) -> PermissionService:
    return PermissionService(session)


def get_role_service(session: AsyncSession = Depends(get_db_session)) -> RoleService:
    return RoleService(session)


def get_refresh_token_service(session: AsyncSession = Depends(get_db_session)) -> RefreshTokenService:
    return RefreshTokenService(session)


def get_user_service(session: AsyncSession = Depends(get_db_session)) -> UserSrvice:
    return UserSrvice(session)


def get_resource_service(session: AsyncSession = Depends(get_db_session)) -> ResourceService:
    return ResourceService(session)


def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
    refresh_token_service: RefreshTokenService = Depends(get_refresh_token_service),
    user_service: UserSrvice = Depends(get_user_service),
) -> AuthService:
    return AuthService(session, refresh_token_service, user_service)
