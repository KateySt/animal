from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.cookies import delete_refresh_cookie, set_refresh_cookie
from app.db import TokenType
from app.schemas.auth import Auth2Redirect, RegisterRequest, Token
from app.schemas.user import UserRead
from app.services import get_auth_service
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> UserRead:
    return await service.register(payload.email, payload.password)


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> Token:
    tokens = await service.login(form.username, form.password)
    set_refresh_cookie(response, tokens)
    return tokens


@router.post("/refresh", response_model=Token)
async def refresh(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> Token:
    tokens = await service.refresh(request.cookies.get(TokenType.refresh))
    set_refresh_cookie(response, tokens)
    return Token(access_token=tokens.access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> None:
    await service.logout(request.cookies.get(TokenType.refresh))
    delete_refresh_cookie(response)


@router.get("/google/authorize", response_model=Auth2Redirect)
async def google_authorize(
    service: AuthService = Depends(get_auth_service),
) -> Auth2Redirect:
    return await service.get_authorize_url()


@router.get("/google/callback", response_model=Token)
async def google_callback(
    code: str,
    state: str,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> Token:
    tokens = await service.google_callback(code, state)
    set_refresh_cookie(response, tokens)
    return Token(access_token=tokens.access_token)
