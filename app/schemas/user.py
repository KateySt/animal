import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.schemas.role import RoleRead


class UserInternal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    hashed_password: str
    is_active: bool
    is_superuser: bool
    is_verified: bool
    permissions_version: int


class RefreshTokenCreate(BaseModel):
    user_id: uuid.UUID
    token_hash: str
    expires_at: datetime


class RefreshTokenInternal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    expires_at: datetime
    is_revoked: bool
    rotated_to: uuid.UUID | None = None


class UserCreate(BaseModel):
    email: EmailStr
    hashed_password: str


class OAuthAccountCreate(BaseModel):
    user_id: uuid.UUID
    oauth_name: str
    account_id: str
    account_email: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    is_active: bool
    is_superuser: bool
    is_verified: bool
    roles: list[RoleRead] = []


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
