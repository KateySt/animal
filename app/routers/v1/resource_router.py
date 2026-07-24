from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_superuser
from app.schemas.resource import ResourceCreate, ResourceRead, ResourceUpdate
from app.services import ResourceService, get_resource_service

router = APIRouter(dependencies=[Depends(require_superuser)])


@router.get("")
async def list_resources(service: ResourceService = Depends(get_resource_service)) -> dict:
    return await service.list_resources()


@router.post("", response_model=ResourceRead, status_code=status.HTTP_201_CREATED)
async def create_resource(payload: ResourceCreate, service: ResourceService = Depends(get_resource_service)) -> ResourceRead:
    return await service.create_resource(payload)


@router.patch("/{resource_id}", response_model=ResourceRead)
async def update_resource(resource_id: UUID, payload: ResourceUpdate, service: ResourceService = Depends(get_resource_service)) -> ResourceRead:
    return await service.update_resource(resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(resource_id: UUID, service: ResourceService = Depends(get_resource_service)) -> None:
    await service.delete_resource(resource_id)
