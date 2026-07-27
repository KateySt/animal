from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import Principal, get_current_user, require_superuser
from app.db.models.user import User
from app.schemas.role import UserRoleAssign
from app.schemas.user import UserRead
from app.services import get_role_service
from app.services.role_service import RoleService

router = APIRouter()


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
