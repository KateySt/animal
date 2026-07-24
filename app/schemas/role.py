import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.permission import PermissionRead


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None


class RoleDetailRead(RoleRead):
    permissions: list[PermissionRead] = []


class RolePermissionAssign(BaseModel):
    permission_ids: list[uuid.UUID] = Field(min_length=1)


class UserRoleAssign(BaseModel):
    role_ids: list[uuid.UUID] = Field(min_length=1)
