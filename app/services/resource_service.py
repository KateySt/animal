import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.exceptions import AlreadyExistsError, BadRequestError, NotFoundError
from app.db.models import Resource, permission_crud, resource_crud
from app.schemas.resource import ResourceCreate, ResourceRead, ResourceUpdate


# todo add logic to validate resource name
class ResourceService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_resource_by_name(self, name: str) -> ResourceRead:
        resource = await resource_crud.get(self._session, name=name, schema_to_select=ResourceRead)
        if resource is None:
            raise NotFoundError(ErrorCode.RESOURCE_NOT_FOUND)
        return resource

    async def get_resource(self, resource_id: uuid.UUID) -> ResourceRead:
        resource = await resource_crud.get(self._session, id=resource_id, schema_to_select=ResourceRead)
        if resource is None:
            raise NotFoundError(ErrorCode.RESOURCE_NOT_FOUND)
        return resource

    async def list_resources(self) -> dict:
        return await resource_crud.get_multi(self._session, limit=None, return_total_count=False)

    async def create_resource(self, payload: ResourceCreate) -> ResourceRead:
        if await resource_crud.exists(self._session, name=payload.name):
            raise AlreadyExistsError(ErrorCode.RESOURCE_ALREADY_EXISTS)

        return await resource_crud.create(self._session, payload, schema_to_select=ResourceRead)

    async def update_resource(self, resource_id: uuid.UUID, payload: ResourceUpdate) -> Resource:
        await self.get_resource(resource_id)
        return await resource_crud.update(
            self._session, payload.model_dump(exclude_unset=True), return_columns=resource_crud.model_col_names,
            id=resource_id
        )

    async def delete_resource(self, resource_id: uuid.UUID) -> None:
        await self.get_resource(resource_id)
        has_permissions = await permission_crud.exists(self._session, resource_id=resource_id)
        if has_permissions:
            raise BadRequestError(ErrorCode.RESOURCE_HAS_PERMISSIONS)
        await resource_crud.delete(self._session, id=resource_id)
