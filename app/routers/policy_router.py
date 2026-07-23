from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_superuser
from app.db.models.user import User
from app.schemas.policy import PermissionCreate, PermissionResponse
from app.services import get_permission_service
from app.services.permission_service import PermissionService

router = APIRouter()


@router.get("", response_model=dict[str, Any])
async def list_permissions(
    service: PermissionService = Depends(get_permission_service),
    _: User = Depends(require_superuser),
)-> dict[str, Any]:
    return await service.list_permissions()


@router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def add_permission(
    payload: PermissionCreate,
    service: PermissionService = Depends(get_permission_service),
    _: User = Depends(require_superuser),
) -> PermissionResponse:
    return await service.add_permission(payload.role, payload.resource, payload.action)


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_permission(
    permission_id: UUID,
    service: PermissionService = Depends(get_permission_service),
    _: User = Depends(require_superuser),
) -> None:
    await service.remove_permission(permission_id)
