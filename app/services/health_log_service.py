from typing import Any
from uuid import UUID

from fastcrud import compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import NotFoundError
from app.db.models import HealthLog, animal_crud, health_log_crud
from app.schemas.animal import HealthLogCreate, HealthLogInternalCreate, HealthLogRead, HealthLogUpdate


class HealthLogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _ensure_animal_exists(self, animal_id: UUID) -> None:
        if not await animal_crud.exists(self._session, id=animal_id):
            raise NotFoundError(f"Animal with id {animal_id} not found")

    async def get_health_log_by_id(self, animal_id: UUID, health_log_id: UUID) -> HealthLogRead:
        await self._ensure_animal_exists(animal_id)
        health_log = await health_log_crud.get(
            self._session,
            schema_to_select=HealthLogRead,
            return_as_model=True,
            id=health_log_id,
        )
        if health_log is None or health_log.animal_id != animal_id:
            raise NotFoundError(f"HealthLog with id {health_log_id} not found for animal {animal_id}")
        return health_log

    async def get_logs_paginated(self, animal_id: UUID, page: int, items_per_page: int) -> dict[str, Any]:
        await self._ensure_animal_exists(animal_id)
        crud_data = await health_log_crud.get_multi(
            self._session,
            offset=compute_offset(page, items_per_page),
            limit=items_per_page,
            return_total_count=True,
            schema_to_select=HealthLogRead,
            return_as_model=True,
            animal_id=animal_id,
        )
        return paginated_response(crud_data=crud_data, page=page, items_per_page=items_per_page)

    async def create_log(self, animal_id: UUID, payload: HealthLogCreate) -> HealthLog:
        await self._ensure_animal_exists(animal_id)
        return await health_log_crud.create(
            self._session,
            HealthLogInternalCreate(animal_id=animal_id, **payload.model_dump()),
            schema_to_select=HealthLogRead,  # it was added because lib doesn't support return dict without it(
        )

    async def update_log(self, animal_id: UUID, health_log_id: UUID, payload: HealthLogUpdate) -> HealthLog:
        await self.get_health_log_by_id(animal_id, health_log_id)
        return await health_log_crud.update(
            self._session,
            payload.model_dump(exclude_none=True),
            return_columns=health_log_crud.model_col_names,  # to get whole model
            id=health_log_id,
        )

    async def delete_log(self, animal_id: UUID, health_log_id: UUID) -> None:
        await self.get_health_log_by_id(animal_id, health_log_id)
        await health_log_crud.delete(self._session, id=health_log_id)
