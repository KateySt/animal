from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.error_codes import ErrorCode
from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.db.models import Permission, permission_crud, resource_crud
from app.db.models.associations import role_permissions, user_roles
from app.db.models.user import User
from app.schemas.permission import PermissionCreate, PermissionRead
from app.services.redis_service import redis_service


class PermissionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_permissions(self) -> dict:
        result = await self._session.execute(select(Permission).options(selectinload(Permission.resource)))
        return {"data": [PermissionRead.model_validate(permission) for permission in result.scalars().all()]}

    async def create_permission(self, payload: PermissionCreate) -> Permission:
        if not await resource_crud.exists(self._session, id=payload.resource_id):
            raise NotFoundError(ErrorCode.RESOURCE_NOT_FOUND)

        if await permission_crud.exists(self._session, resource_id=payload.resource_id, action=payload.action):
            raise AlreadyExistsError(ErrorCode.PERMISSION_ALREADY_EXISTS)

        await permission_crud.create(self._session, payload)
        result = await self._session.execute(
            select(Permission)
            .where(Permission.resource_id == payload.resource_id, Permission.action == payload.action)
            .options(selectinload(Permission.resource))
        )
        return result.scalar_one()

    async def get_permission(self, permission_id: UUID) -> Permission:
        permission = await permission_crud.get(self._session, id=permission_id)
        if permission is None:
            raise NotFoundError(ErrorCode.PERMISSION_NOT_FOUND)
        return permission

    async def check_permission(self, permission_id: UUID) -> None:
        if not await permission_crud.exists(self._session, id=permission_id):
            raise NotFoundError(ErrorCode.PERMISSION_NOT_FOUND)

    async def delete_permission(self, permission_id: UUID) -> None:
        await self.check_permission(permission_id)

        updated_version_users = await self._session.execute(
            update(User)
            .where(
                User.id.in_(
                    select(user_roles.c.user_id)
                    .join(role_permissions, role_permissions.c.role_id == user_roles.c.role_id)
                    .where(role_permissions.c.permission_id == permission_id)
                    .distinct()
                    .scalar_subquery()
                )
            )
            .values(permissions_version=User.permissions_version + 1)
            .returning(User.id)
        )

        await permission_crud.delete(self._session, id=permission_id)

        for user in updated_version_users.scalars().all():
            await redis_service.delete_cache(f"permissions_version:{user}")
