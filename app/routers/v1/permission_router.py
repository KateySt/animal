from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_superuser
from app.schemas.permission import PermissionCreate, PermissionRead
from app.services import get_permission_service
from app.services.permission_service import PermissionService

router = APIRouter(dependencies=[Depends(require_superuser)])


@router.get("")
async def list_permissions(service: PermissionService = Depends(get_permission_service)) -> dict:
    return await service.list_permissions()


@router.post("", response_model=PermissionRead, status_code=status.HTTP_201_CREATED)
async def create_permission(
    payload: PermissionCreate,
    service: PermissionService = Depends(get_permission_service)
) -> PermissionRead:
    return await service.create_permission(payload)


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(permission_id: UUID, service: PermissionService = Depends(get_permission_service)) -> None:
    await service.delete_permission(permission_id)
