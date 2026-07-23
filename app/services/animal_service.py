from typing import Any
from uuid import UUID

from fastcrud import compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import NotFoundError
from app.db.models import Animal, HealthLog, animal_crud, health_log_crud
from app.schemas.animal import (
    AnimalCreate,
    AnimalResponse,
    AnimalUpdate,
    HealthLogInternalCreate,
    HealthLogResponse,
)


class AnimalService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_animal_by_id(self, id: UUID) -> Animal:
        animal = await animal_crud.get_joined(
            db=self._session,
            join_model=HealthLog,
            join_on=HealthLog.animal_id == Animal.id,
            join_prefix="health_logs_",
            join_type="left",
            nest_joins=True,
            relationship_type="one-to-many",
            id=id,
        )
        if animal is None:
            raise NotFoundError(f"Animal with id {id} not found")
        return animal

    async def get_animals_paginated(
        self,
        page: int,
        items_per_page: int,
    ) -> dict[str, Any]:
        crud_data = await animal_crud.get_multi_joined(
            self._session,
            join_model=HealthLog,
            join_on=HealthLog.animal_id == Animal.id,
            join_prefix="health_logs_",
            join_schema_to_select=HealthLogResponse,
            join_type="left",
            nest_joins=True,
            relationship_type="one-to-many",
            schema_to_select=AnimalResponse,
            offset=compute_offset(page, items_per_page),
            limit=items_per_page,
            return_total_count=True,
        )
        return paginated_response(crud_data=crud_data, page=page, items_per_page=items_per_page)

    async def create_animal_with_initial_health_log(self, payload: AnimalCreate) -> Animal:
        async with self._session.begin_nested():
            animal = Animal(**payload.model_dump(exclude={"health_logs"}))
            self._session.add(animal)
            await self._session.flush()
            log_schemas = [HealthLogInternalCreate(animal_id=animal.id, **log.model_dump()) for log in payload.health_logs]
            await health_log_crud.upsert_multi(self._session, log_schemas, commit=False)
        await self._session.commit()
        return await self.get_animal_by_id(animal.id)

    async def update_animal(self, id: UUID, payload: AnimalUpdate) -> Animal:
        await self.get_animal_by_id(id)
        return await animal_crud.update(
            self._session,
            payload.model_dump(exclude_none=True),
            return_columns=animal_crud.model_col_names,# to get whole model
            id=id
        )

    async def delete_animal(self, id: UUID) -> None:
        await self.get_animal_by_id(id)
        await animal_crud.delete(self._session, id=id)
