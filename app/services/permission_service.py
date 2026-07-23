from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.db.enums import Policy, Role
from app.db.models import permission_crud
from app.schemas.policy import PermissionCreate, PermissionResponse


class PermissionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_permissions(self):
        return await permission_crud.get_multi(self._session, schema_to_select=PermissionResponse, return_as_model=True)

    async def get_permission(self, permission_id: UUID) -> dict:
        permission = await permission_crud.get(self._session, id=permission_id)
        if permission is None:
            raise NotFoundError(f"Permission {permission_id} not found")
        return permission

    async def add_permission(self, role: Role, resource: str, action: Policy) -> dict:
        existing = await permission_crud.get(self._session, role=role, resource=resource, action=action)
        if existing is not None:
            raise AlreadyExistsError(f"Permission {role}:{resource}:{action} already exists")

        return await permission_crud.create(
            self._session,
            PermissionCreate(role=role, resource=resource, action=action),
            schema_to_select=PermissionResponse,#it was added because lib doesn't support return dict without it(
        )

    async def remove_permission(self, permission_id: UUID) -> None:
        await self.get_permission(permission_id)
        await permission_crud.delete(self._session, id=permission_id)
