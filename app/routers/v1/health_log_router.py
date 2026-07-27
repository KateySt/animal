from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastcrud import PaginatedListResponse

from app.core.dependencies import require_scopes
from app.db.models import HealthLog
from app.schemas import Principal
from app.schemas.animal import HealthLogCreate, HealthLogRead, HealthLogUpdate
from app.services import get_health_log_service
from app.services.health_log_service import HealthLogService

router = APIRouter()


@router.get("", response_model=PaginatedListResponse[HealthLogRead])
async def get_health_logs(
    animal_id: UUID,
    page: int = Query(1, ge=1),
    items_per_page: int = Query(20, ge=1, le=100),
    service: HealthLogService = Depends(get_health_log_service),
    _: Principal = Depends(require_scopes(f"{HealthLog.subject()}:read")),
) -> dict[str, Any]:
    return await service.get_logs_paginated(animal_id, page, items_per_page)


@router.get("/{health_log_id}", response_model=HealthLogRead)
async def get_health_log(
    animal_id: UUID,
    health_log_id: UUID,
    service: HealthLogService = Depends(get_health_log_service),
    _: Principal = Depends(require_scopes(f"{HealthLog.subject()}:read")),
) -> HealthLog:
    return await service.get_health_log_by_id(animal_id, health_log_id)


@router.post("", response_model=HealthLogRead, status_code=status.HTTP_201_CREATED)
async def create_health_log(
    animal_id: UUID,
    payload: HealthLogCreate,
    service: HealthLogService = Depends(get_health_log_service),
    _: Principal = Depends(require_scopes(f"{HealthLog.subject()}:create")),
) -> HealthLog:
    return await service.create_log(animal_id, payload)


@router.patch("/{health_log_id}", response_model=HealthLogRead)
async def update_health_log(
    animal_id: UUID,
    health_log_id: UUID,
    payload: HealthLogUpdate,
    service: HealthLogService = Depends(get_health_log_service),
    _: Principal = Depends(require_scopes(f"{HealthLog.subject()}:update")),
) -> HealthLog:
    return await service.update_log(animal_id, health_log_id, payload)


@router.delete("/{health_log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_health_log(
    animal_id: UUID,
    health_log_id: UUID,
    service: HealthLogService = Depends(get_health_log_service),
    _: Principal = Depends(require_scopes(f"{HealthLog.subject()}:delete")),
) -> None:
    await service.delete_log(animal_id, health_log_id)
