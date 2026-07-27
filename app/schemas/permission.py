import uuid

from pydantic import BaseModel, ConfigDict


class PermissionCreate(BaseModel):
    resource_id: uuid.UUID
    action: str


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resource_id: uuid.UUID
    action: str
    scope: str
