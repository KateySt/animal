from typing import Any
from uuid import UUID

from fastcrud import compute_offset, paginated_response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import NotFoundError
from app.db.models import Animal, animal_crud, health_log_crud
from app.schemas.animal import AnimalCreate, AnimalInternalCreate, AnimalResponse, AnimalWithHealthLogsResponse, AnimalUpdate, HealthLogInternalCreate


class AnimalService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_animal_by_id(self, id: UUID) -> Animal:
        result = await self._session.execute(select(Animal).options(selectinload(Animal.health_logs)).where(Animal.id == id))
        animal = result.scalar_one_or_none()
        if animal is None:
            raise NotFoundError(f"Animal with id {id} not found")
        return animal

    async def get_animals_paginated(
        self,
        page: int,
        items_per_page: int,
    ) -> dict[str, Any]:
        crud_data = await animal_crud.get_multi(
            self._session,
            offset=compute_offset(page, items_per_page),
            limit=items_per_page,
            return_total_count=True,
            schema_to_select=AnimalResponse,
            return_as_model=True,
        )
        return paginated_response(crud_data=crud_data, page=page, items_per_page=items_per_page)

    async def create_animal_with_initial_health_log(self, payload: AnimalCreate) -> AnimalWithHealthLogsResponse:
        async with self._session.begin():
            animal = Animal(**AnimalInternalCreate(**payload.model_dump(exclude={"health_logs"})).model_dump())
            self._session.add(animal)
            await self._session.flush()

            for log_data in payload.health_logs:
                await health_log_crud.create(
                    self._session,
                    HealthLogInternalCreate(animal_id=animal.id, **log_data.model_dump()),
                    commit=False,
                )

        return await self.get_animal_by_id(animal.id)

    async def update_animal(self, id: UUID, payload: AnimalUpdate) -> Animal:
        await self.get_animal_by_id(id)
        await animal_crud.update(self._session, payload.model_dump(exclude_none=True), id=id)
        return await self.get_animal_by_id(id)

    async def delete_animal(self, id: UUID) -> None:
        await self.get_animal_by_id(id)
        await animal_crud.delete(self._session, id=id)
