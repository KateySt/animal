from uuid import UUID

from app.core import NotFoundError
from app.db.models.health_log import HealthLog
from app.repo.animal_repository import AnimalRepository
from app.repo.health_log_repository import HealthLogRepository
from app.schemas import PaginatedResult
from app.schemas.animal import HealthLogCreate, HealthLogResponse, HealthLogUpdate


class HealthLogService:
    def __init__(self, health_log_repo: HealthLogRepository, animal_repo: AnimalRepository) -> None:
        self._health_log_repo = health_log_repo
        self._animal_repo = animal_repo

    async def _ensure_animal_exists(self, animal_id: UUID) -> None:
        if not await self._animal_repo.get_by_id(animal_id):
            raise NotFoundError(f"Animal with id {animal_id} not found")

    async def get_health_log_by_id(self, animal_id: UUID, health_log_id: UUID) -> HealthLog:
        await self._ensure_animal_exists(animal_id)
        log = await self._health_log_repo.get_by_id(health_log_id)
        if log is None or log.animal_id != animal_id:
            raise NotFoundError(f"HealthLog with id {health_log_id} not found for animal {animal_id}")
        return log

    async def get_logs_paginated(self, animal_id: UUID, page: int, page_size: int) -> PaginatedResult[HealthLogResponse]:
        await self._ensure_animal_exists(animal_id)
        return await self._health_log_repo.get_paginated(
            page=page,
            page_size=page_size,
            filters={"animal_id": animal_id},
        )

    async def create_log(self, animal_id: UUID, payload: HealthLogCreate) -> HealthLog:
        await self._ensure_animal_exists(animal_id)
        return await self._health_log_repo.create(HealthLog(animal_id=animal_id, **payload.model_dump()))

    async def update_log(self, animal_id: UUID, health_log_id: UUID, payload: HealthLogUpdate) -> HealthLog:
        await self.get_health_log_by_id(animal_id, health_log_id)
        updated = await self._health_log_repo.update(health_log_id, payload.model_dump(exclude_none=True))
        if updated is None:
            raise NotFoundError(f"HealthLog with id {health_log_id} not found")
        return updated

    async def delete_log(self, animal_id: UUID, health_log_id: UUID) -> None:
        await self.get_health_log_by_id(animal_id, health_log_id)
        await self._health_log_repo.delete(health_log_id)
