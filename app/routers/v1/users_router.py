from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, status

from app.core.dependencies import Principal, get_current_user, require_superuser
from app.db.models.user import User
from app.schemas.role import UserRoleAssign
from app.schemas.user import UserRead
from app.services import get_role_service, get_user_service
from app.services.role_service import RoleService
from app.services.user_service import UserService

router = APIRouter()


@router.get("", response_model=list[UserRead])
async def list_users(
    service: UserService = Depends(get_user_service),
    _: Principal = Depends(require_superuser),
) -> list[UserRead]:
    return await service.list_users()


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)) -> UserRead:
    return user


@router.put("/{user_id}/roles", response_model=UserRead)
async def assign_roles(
    user_id: UUID,
    payload: UserRoleAssign,
    service: RoleService = Depends(get_role_service),
    _: Principal = Depends(require_superuser),
) -> UserRead:
    return await service.assign_roles_to_user(user_id, payload.role_ids)


@router.put("/me/avatar", response_model=UserRead)
async def upload_avatar(
    file: UploadFile,
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    file_data = await file.read()
    return await service.upload_avatar(user, file.content_type or "", file_data)


@router.delete("/me/avatar", status_code=status.HTTP_204_NO_CONTENT)
async def delete_avatar(
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> None:
    await service.delete_avatar(user)
