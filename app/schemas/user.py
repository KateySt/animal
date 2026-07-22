import datetime
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class UserWithPassword(UserResponse):
    hashed_password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class UserInternalCreate(BaseModel):
    name: str
    email: EmailStr
    hashed_password: str
