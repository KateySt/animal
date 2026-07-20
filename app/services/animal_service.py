from uuid import UUID

from app.core import NotFoundError
from app.db.models.animal import Animal
from app.db.models.health_log import HealthLog
from app.repo import AnimalRepository
from app.repo.health_log_repository import HealthLogRepository
from app.schemas import PaginatedResult
from app.schemas.animal import AnimalCreate, AnimalUpdate, AnimalResponse


class AnimalService:
    def __init__(self, animal_repo: AnimalRepository, health_log_repo: HealthLogRepository) -> None:
        self._animal_repo = animal_repo
        self._health_log_repo = health_log_repo

    async def get_animal_by_id(self, id: UUID) -> Animal:
        if animal := await self._animal_repo.get_by_id(id):
            return animal
        raise NotFoundError(f"Animal with id {id} not found")

    async def get_animals_paginated(
        self,
        page: int,
        page_size: int,
        filters: dict | None = None,
        order_by: list[str] | None = None,
    ) -> PaginatedResult[AnimalResponse]:
        return await self._animal_repo.get_paginated(page=page, page_size=page_size, filters=filters, order_by=order_by)

    async def create_animal_with_initial_health_log(self, payload: AnimalCreate) -> Animal:
        animal = await self._animal_repo.create(Animal(**payload.model_dump(exclude={"health_logs"})))
        for log_data in payload.health_logs:
            await self._health_log_repo.create(HealthLog(animal_id=animal.id, **log_data.model_dump()))
        return await self.get_animal_by_id(animal.id)

    async def update_animal(self, id: UUID, payload: AnimalUpdate) -> Animal:
        updated = await self._animal_repo.update(id, payload.model_dump(exclude_none=True))
        if updated is None:
            raise NotFoundError(f"Animal with id {id} not found")
        return updated

    async def delete_animal(self, id: UUID) -> None:
        deleted = await self._animal_repo.delete(id)
        if not deleted:
            raise NotFoundError(f"Animal with id {id} not found")
