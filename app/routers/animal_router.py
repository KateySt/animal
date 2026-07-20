from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.schemas import PaginatedResult
from app.schemas.animal import AnimalCreate, AnimalResponse, AnimalUpdate
from app.services import get_animal_service
from app.services.animal_service import AnimalService

router = APIRouter()


@router.get("", response_model=PaginatedResult[AnimalResponse])
async def get_animals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: str | None = Query(None),
    gender: str | None = Query(None),
    order_by: list[str] = Query(default=[]),
    service: AnimalService = Depends(get_animal_service),
) -> PaginatedResult[AnimalResponse]:
    filters: dict = {}
    if name:
        filters["name__like"] = name
    if gender:
        filters["gender"] = gender
    return await service.get_animals_paginated(
        page=page,
        page_size=page_size,
        filters=filters or None,
        order_by=order_by or None
    )


@router.get("/{animal_id}", response_model=AnimalResponse)
async def get_animal(
    animal_id: UUID,
    service: AnimalService = Depends(get_animal_service),
) -> AnimalResponse:
    return await service.get_animal_by_id(animal_id)


@router.post("", response_model=AnimalResponse, status_code=status.HTTP_201_CREATED)
async def create_animal(
    payload: AnimalCreate,
    service: AnimalService = Depends(get_animal_service),
) -> AnimalResponse:
    return await service.create_animal_with_initial_health_log(payload)


@router.patch("/{animal_id}", response_model=AnimalResponse)
async def update_animal(
    animal_id: UUID,
    payload: AnimalUpdate,
    service: AnimalService = Depends(get_animal_service),
) -> AnimalResponse:
    return await service.update_animal(animal_id, payload)


@router.delete("/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_animal(
    animal_id: UUID,
    service: AnimalService = Depends(get_animal_service),
) -> None:
    await service.delete_animal(animal_id)
