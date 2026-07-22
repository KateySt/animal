from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core import UnauthorizedError
from app.core.security import decode_token
from app.db import TokenType
from app.schemas import UserResponse
from app.services import UserService, get_user_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    payload = decode_token(token)

    if payload.get("type") != TokenType.access:
        raise UnauthorizedError("Invalid token type")

    return await service.get_by_email(payload.get("sub"))
