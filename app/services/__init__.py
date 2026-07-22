from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.services.animal_service import AnimalService
from app.services.health_log_service import HealthLogService
from app.services.redis_service import RedisService
from app.services.user_service import UserService


def get_animal_service(session: AsyncSession = Depends(get_db_session)) -> AnimalService:
    return AnimalService(session)


def get_health_log_service(session: AsyncSession = Depends(get_db_session)) -> HealthLogService:
    return HealthLogService(session)


def get_redis_service() -> RedisService:
    return RedisService()


def get_user_service(
    session: AsyncSession = Depends(get_db_session),
    redis: RedisService = Depends(get_redis_service),
) -> UserService:
    return UserService(session, redis)
