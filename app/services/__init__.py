from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.repo.animal_repository import AnimalRepository
from app.repo.health_log_repository import HealthLogRepository
from app.services.animal_service import AnimalService


def get_animal_service(session: AsyncSession = Depends(get_db_session)) -> AnimalService:
    return AnimalService(AnimalRepository(session), HealthLogRepository(session))
