from typing import Any
from uuid import UUID

from fastcrud import compute_offset, paginated_response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import NotFoundError
from app.core.error_codes import ErrorCode
from app.db.models import HealthLog, HealthLogTranslation, animal_crud, health_log_crud
from app.schemas.animal import HealthLogCreate, HealthLogUpdate


class HealthLogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _ensure_animal_exists(self, animal_id: UUID) -> None:
        if not await animal_crud.exists(self._session, id=animal_id):
            raise NotFoundError(ErrorCode.ANIMAL_NOT_FOUND)

    async def get_health_log_by_id(self, animal_id: UUID, health_log_id: UUID) -> HealthLog:
        result = await self._session.execute(
            select(HealthLog).where(HealthLog.id == health_log_id, HealthLog.animal_id == animal_id).options(selectinload(HealthLog.translations))
        )
        log = result.scalar_one_or_none()
        if log is None:
            raise NotFoundError(ErrorCode.HEALTH_LOG_NOT_FOUND)
        return log

    async def get_logs_paginated(self, animal_id: UUID, page: int, items_per_page: int) -> dict[str, Any]:
        await self._ensure_animal_exists(animal_id)
        offset = compute_offset(page, items_per_page)

        total_result = await self._session.execute(select(func.count()).select_from(HealthLog).where(HealthLog.animal_id == animal_id))

        result = await self._session.execute(
            select(HealthLog)
            .where(HealthLog.animal_id == animal_id)
            .options(selectinload(HealthLog.translations))
            .offset(offset)
            .limit(items_per_page)
        )

        return paginated_response(
            crud_data={"data": result.scalars().all(), "total_count": total_result.scalar_one()},
            page=page,
            items_per_page=items_per_page,
        )

    async def create_log(self, animal_id: UUID, payload: HealthLogCreate) -> HealthLog:
        await self._ensure_animal_exists(animal_id)
        log = HealthLog(animal_id=animal_id)
        self._session.add(log)
        await self._session.flush()
        self._session.add_all(HealthLogTranslation(parent_id=log.id, **translation.model_dump()) for translation in payload.translations)
        await self._session.commit()
        result = await self._session.execute(select(HealthLog).where(HealthLog.id == log.id).options(selectinload(HealthLog.translations)))
        return result.scalar_one()

    async def update_log(self, animal_id: UUID, health_log_id: UUID, payload: HealthLogUpdate) -> HealthLog:
        log = await self.get_health_log_by_id(animal_id, health_log_id)
        if payload.translations is not None:
            existing_by_locale = {translation.locale: translation for translation in log.translations}

            for translation_payload in payload.translations:
                existing = existing_by_locale.get(translation_payload.locale)
                if existing:
                    existing.procedure_name = translation_payload.procedure_name
                    existing.examination_findings = translation_payload.examination_findings
                else:
                    self._session.add(HealthLogTranslation(parent_id=log.id, **translation_payload.model_dump()))

        await self._session.commit()
        return await self.get_health_log_by_id(animal_id, health_log_id)

    async def delete_log(self, animal_id: UUID, health_log_id: UUID) -> None:
        await self.get_health_log_by_id(animal_id, health_log_id)
        await health_log_crud.delete(self._session, id=health_log_id)
