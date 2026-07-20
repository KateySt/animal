from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.schemas import PaginatedResult
from app.schemas.animal import HealthLogCreate, HealthLogResponse, HealthLogUpdate
from app.services import get_health_log_service
from app.services.health_log_service import HealthLogService

router = APIRouter()


@router.get("", response_model=PaginatedResult[HealthLogResponse])
async def get_health_logs(
    animal_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: HealthLogService = Depends(get_health_log_service),
) -> PaginatedResult[HealthLogResponse]:
    return await service.get_logs_paginated(animal_id, page, page_size)


@router.get("/{log_id}", response_model=HealthLogResponse)
async def get_health_log(
    animal_id: UUID,
    health_log_id: UUID,
    service: HealthLogService = Depends(get_health_log_service),
) -> HealthLogResponse:
    return await service.get_health_log_by_id(animal_id, health_log_id)


@router.post("", response_model=HealthLogResponse, status_code=status.HTTP_201_CREATED)
async def create_health_log(
    animal_id: UUID,
    payload: HealthLogCreate,
    service: HealthLogService = Depends(get_health_log_service),
) -> HealthLogResponse:
    return await service.create_log(animal_id, payload)


@router.patch("/{log_id}", response_model=HealthLogResponse)
async def update_health_log(
    animal_id: UUID,
    health_log_id: UUID,
    payload: HealthLogUpdate,
    service: HealthLogService = Depends(get_health_log_service),
) -> HealthLogResponse:
    return await service.update_log(animal_id, health_log_id, payload)


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_health_log(
    animal_id: UUID,
    health_log_id: UUID,
    service: HealthLogService = Depends(get_health_log_service),
) -> None:
    await service.delete_log(animal_id, health_log_id)
