from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.services.animal_service import AnimalService
from app.services.health_log_service import HealthLogService


def get_animal_service(session: AsyncSession = Depends(get_db_session)) -> AnimalService:
    return AnimalService(session)


def get_health_log_service(session: AsyncSession = Depends(get_db_session)) -> HealthLogService:
    return HealthLogService(session)
