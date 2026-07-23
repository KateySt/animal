import uuid

from pydantic import BaseModel, ConfigDict

from app.db.enums import Policy, Role


class PermissionCreate(BaseModel):
    role: Role
    resource: str
    action: Policy


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: Role
    resource: str
    action: Policy
