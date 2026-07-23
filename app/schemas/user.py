import uuid

from fastapi_users import schemas

from app.db.enums import Role


class UserRead(schemas.BaseUser[uuid.UUID]):
    role: Role


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    role: Role | None = None
