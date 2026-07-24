from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class IssuedTokens(BaseModel):
    access_token: str
    refresh_token: str
    refresh_expires_at: datetime


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Auth2Redirect(BaseModel):
    authorization_url: str


class Principal(BaseModel):
    user_id: UUID
    is_superuser: bool = False
    scopes: list[str] = []
