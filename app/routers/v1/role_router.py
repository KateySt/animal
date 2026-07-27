from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_superuser
from app.schemas.role import RoleCreate, RoleDetailRead, RolePermissionAssign, RoleRead, RoleUpdate
from app.services import get_role_service
from app.services.role_service import RoleService

router = APIRouter(dependencies=[Depends(require_superuser)])


@router.get("")
async def list_roles(service: RoleService = Depends(get_role_service)) -> dict:
    return await service.list_roles()


@router.get("/{role_id}", response_model=RoleDetailRead)
async def get_role(role_id: UUID, service: RoleService = Depends(get_role_service)) -> RoleDetailRead:
    return await service.get_role(role_id)


@router.post("", response_model=RoleDetailRead, status_code=status.HTTP_201_CREATED)
async def create_role(payload: RoleCreate, service: RoleService = Depends(get_role_service)) -> RoleDetailRead:
    return await service.create_role(payload)


@router.patch("/{role_id}", response_model=RoleDetailRead)
async def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    service: RoleService = Depends(get_role_service)
) -> RoleDetailRead:
    return await service.update_role(role_id, payload)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: UUID, service: RoleService = Depends(get_role_service)) -> None:
    await service.delete_role(role_id)


@router.put("/{role_id}/permissions", response_model=RoleDetailRead)
async def set_role_permissions(
    role_id: UUID,
    payload: RolePermissionAssign,
    service: RoleService = Depends(get_role_service)
) -> RoleDetailRead:
    return await service.set_role_permissions(role_id, payload.permission_ids)
