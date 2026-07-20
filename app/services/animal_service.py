from uuid import UUID

from app.core import NotFoundError
from app.db.models.animal import Animal
from app.repo import AnimalRepository
from app.repo.health_log_repository import HealthLogRepository
from app.schemas.animal import AnimalCreate


class AnimalService:
    def __init__(self, animal_repo: AnimalRepository, health_log_repo: HealthLogRepository) -> None:
        self._animal_repo = animal_repo
        self._health_log_repo = health_log_repo

    async def get_animal_by_id(self, id: UUID) -> Animal:
        if animal := await self._animal_repo.get_by_id(id):
            return animal
        raise NotFoundError(f"Animal with id {id} not found")

    async def create_animal_with_initial_health_log(self, payload: AnimalCreate) -> Animal:
        animal = await self._animal_repo.create(payload.to_animal())
        for health_log in payload.to_health_logs(animal.id):
            await self._health_log_repo.create(health_log)
        return await self.get_animal_by_id(animal.id)
