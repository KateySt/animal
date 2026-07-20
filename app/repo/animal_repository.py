from sqlalchemy import Select
from sqlalchemy.orm import selectinload

from app.db.models.animal import Animal
from app.repo.base_repository import BaseRepository


class AnimalRepository(BaseRepository[Animal]):
    model = Animal

    def _base_query(self) -> Select:
        # avoids N+1 queries when callers access health_logs on the returned animals
        return super()._base_query().options(selectinload(Animal.health_logs))
