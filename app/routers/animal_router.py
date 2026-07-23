from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi_cache.decorator import cache
from fastcrud import PaginatedListResponse

from app.core.dependencies import require_permission
from app.db import Policy
from app.db.models import Animal
from app.schemas.animal import AnimalCreate, AnimalResponse, AnimalUpdate
from app.services import get_animal_service
from app.services.animal_service import AnimalService

router = APIRouter()


@router.get("", response_model=PaginatedListResponse[AnimalResponse])
@cache(expire=60)
async def get_animals(
    page: int = Query(1, ge=1),
    items_per_page: int = Query(20, ge=1, le=100),
    service: AnimalService = Depends(get_animal_service),
    _=Depends(require_permission(Animal.subject(), Policy.read)),
) -> dict[str, Any]:
    return await service.get_animals_paginated(page=page, items_per_page=items_per_page)


@router.get("/{animal_id}", response_model=AnimalResponse)
async def get_animal(
    animal_id: UUID,
    service: AnimalService = Depends(get_animal_service),
    _=Depends(require_permission(Animal.subject(), Policy.read)),
) -> AnimalResponse:
    return await service.get_animal_by_id(animal_id)


@router.post("", response_model=AnimalResponse, status_code=status.HTTP_201_CREATED)
async def create_animal(
    payload: AnimalCreate,
    service: AnimalService = Depends(get_animal_service),
    _=Depends(require_permission(Animal.subject(), Policy.create)),
) -> AnimalResponse:
    return await service.create_animal_with_initial_health_log(payload)


@router.patch("/{animal_id}", response_model=AnimalResponse)
async def update_animal(
    animal_id: UUID,
    payload: AnimalUpdate,
    service: AnimalService = Depends(get_animal_service),
    _=Depends(require_permission(Animal.subject(), Policy.update)),
) -> AnimalResponse:
    return await service.update_animal(animal_id, payload)


@router.delete("/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_animal(
    animal_id: UUID,
    service: AnimalService = Depends(get_animal_service),
    _=Depends(require_permission(Animal.subject(), Policy.delete)),
) -> None:
    await service.delete_animal(animal_id)
