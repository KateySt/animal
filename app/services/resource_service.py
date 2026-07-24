import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsError, NotFoundError, BadRequestError
from app.db.models import Resource, resource_crud, permission_crud
from app.schemas.resource import ResourceCreate, ResourceRead, ResourceUpdate

#todo add logic to validate resource name
class ResourceService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_resource_by_name(self, name: str) -> ResourceRead:
        resource = await resource_crud.get(self._session, name=name, schema_to_select=ResourceRead)
        if resource is None:
            raise NotFoundError(f"Resource '{name}' not found")
        return resource

    async def get_resource(self, resource_id: uuid.UUID) -> ResourceRead:
        resource = await resource_crud.get(self._session, id=resource_id, schema_to_select=ResourceRead)
        if resource is None:
            raise NotFoundError(f"Resource {resource_id} not found")
        return resource

    async def list_resources(self) -> dict:
        return await resource_crud.get_multi(self._session, limit=None, return_total_count=False)

    async def create_resource(self, payload: ResourceCreate) -> ResourceRead:
        if await resource_crud.exists(self._session, name=payload.name):
            raise AlreadyExistsError(f"Resource '{payload.name}' already exists")

        return await resource_crud.create(self._session, payload, schema_to_select=ResourceRead)

    async def update_resource(self, resource_id: uuid.UUID, payload: ResourceUpdate) -> Resource:
        await self.get_resource(resource_id)
        return await resource_crud.update(
            self._session,
            payload.model_dump(exclude_unset=True),
            return_columns=resource_crud.model_col_names,
            id=resource_id
        )

    async def delete_resource(self, resource_id: uuid.UUID) -> None:
        await self.get_resource(resource_id)
        has_permissions = await permission_crud.exists(self._session, resource_id=resource_id)
        if has_permissions:
            raise BadRequestError("Cannot delete resource with existing permissions. Delete permissions first.")
        await resource_crud.delete(self._session, id=resource_id)
