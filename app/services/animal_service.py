from typing import Any
from uuid import UUID

from fastcrud import compute_offset, paginated_response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import NotFoundError
from app.core.error_codes import ErrorCode
from app.db.models import Animal, AnimalTranslation, HealthLog, HealthLogTranslation, animal_crud
from app.schemas.animal import AnimalCreate, AnimalUpdate
from app.services.user_service import UserService


class AnimalService:
    def __init__(self, session: AsyncSession, user_service: UserService) -> None:
        self._session = session
        self._user_service = user_service

    async def get_animal_by_id(self, id: UUID) -> Animal:
        result = await self._session.execute(
            select(Animal)
            .where(Animal.id == id)
            .options(
                selectinload(Animal.translations),
                selectinload(Animal.health_logs).selectinload(HealthLog.translations),
            )
        )
        animal = result.scalar_one_or_none()
        if animal is None:
            raise NotFoundError(ErrorCode.ANIMAL_NOT_FOUND)
        return animal

    async def get_animals_paginated(self, page: int, items_per_page: int) -> dict[str, Any]:
        offset = compute_offset(page, items_per_page)

        total_result = await self._session.execute(select(func.count()).select_from(Animal))

        result = await self._session.execute(
            select(Animal)
            .options(
                selectinload(Animal.translations),
                selectinload(Animal.health_logs).selectinload(HealthLog.translations),
            )
            .offset(offset)
            .limit(items_per_page)
        )

        return paginated_response(
            crud_data={"data": result.scalars().unique().all(), "total_count": total_result.scalar_one()},
            page=page,
            items_per_page=items_per_page,
        )

    async def create_animal_with_initial_health_log(self, payload: AnimalCreate) -> Animal:
        owner = await self._user_service.get_by_id(payload.owner_id)
        animal = Animal(gender=payload.gender, birth_date=payload.birth_date, owner_id=owner.id)
        self._session.add(animal)
        await self._session.flush()

        self._session.add_all(AnimalTranslation(parent_id=animal.id, **translation.model_dump()) for translation in payload.translations)

        for log_payload in payload.health_logs:
            log = HealthLog(animal_id=animal.id)
            self._session.add(log)
            await self._session.flush()
            self._session.add_all(HealthLogTranslation(parent_id=log.id, **translation.model_dump()) for translation in log_payload.translations)

        await self._session.commit()
        return await self.get_animal_by_id(animal.id)

    async def update_animal(self, id: UUID, payload: AnimalUpdate) -> Animal:
        animal = await self.get_animal_by_id(id)

        if payload.gender is not None:
            animal.gender = payload.gender
        if payload.birth_date is not None:
            animal.birth_date = payload.birth_date

        if payload.translations is not None:
            existing_by_locale = {translation.locale: translation for translation in animal.translations}

            for translation_payload in payload.translations:
                existing = existing_by_locale.get(translation_payload.locale)
                if existing:
                    existing.name = translation_payload.name
                    existing.caretaker_notes = translation_payload.caretaker_notes
                else:
                    new_translation = AnimalTranslation(parent_id=id, **translation_payload.model_dump())
                    self._session.add(new_translation)
                    animal.translations.append(new_translation)

        await self._session.commit()
        return animal

    async def delete_animal(self, id: UUID) -> None:
        await self.get_animal_by_id(id)
        await animal_crud.delete(self._session, id=id)
