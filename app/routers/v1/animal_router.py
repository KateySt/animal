from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastcrud import PaginatedListResponse

from app.core.dependencies import require_roles, require_scopes
from app.db.models import Animal
from app.schemas import Principal
from app.schemas.animal import AnimalCreate, AnimalRead, AnimalUpdate
from app.services import get_animal_service
from app.services.animal_service import AnimalService

router = APIRouter()


@router.get("", response_model=PaginatedListResponse[AnimalRead])
async def get_animals(
    page: int = Query(1, ge=1),
    items_per_page: int = Query(20, ge=1, le=100),
    service: AnimalService = Depends(get_animal_service),
    _: Principal = Depends(require_scopes(f"{Animal.subject()}:read")),
) -> dict[str, Any]:
    return await service.get_animals_paginated(page=page, items_per_page=items_per_page)


@router.get("/{animal_id}", response_model=AnimalRead)
async def get_animal(
    animal_id: UUID,
    service: AnimalService = Depends(get_animal_service),
    _: Principal = Depends(require_scopes(f"{Animal.subject()}:read")),
) -> Animal:
    return await service.get_animal_by_id(animal_id)


@router.post("", response_model=AnimalRead, status_code=status.HTTP_201_CREATED)
async def create_animal(
    payload: AnimalCreate,
    service: AnimalService = Depends(get_animal_service),
    _: Principal = Depends(require_roles("vet", "admin")),
) -> Animal:
    return await service.create_animal_with_initial_health_log(payload)


@router.patch("/{animal_id}", response_model=AnimalRead)
async def update_animal(
    animal_id: UUID,
    payload: AnimalUpdate,
    service: AnimalService = Depends(get_animal_service),
    _: Principal = Depends(require_scopes(f"{Animal.subject()}:update")),
) -> Animal:
    return await service.update_animal(animal_id, payload)


@router.delete("/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_animal(
    animal_id: UUID,
    service: AnimalService = Depends(get_animal_service),
    _: Principal = Depends(require_scopes(f"{Animal.subject()}:delete")),
) -> None:
    await service.delete_animal(animal_id)
