from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import RedirectResponse

from app.core import get_auth_config
from app.core.cookies import delete_refresh_cookie, set_refresh_cookie
from app.core.oauth import oauth
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
async def google_authorize(request: Request) -> Auth2Redirect:
    google = oauth.create_client("google")
    return await google.authorize_redirect(request, redirect_uri=get_auth_config().GOOGLE_REDIRECT_URI)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    tokens = await service.google_callback(await oauth.google.authorize_access_token(request))
    redirect = RedirectResponse(
        url=f"{get_auth_config().FRONTEND_URL}/auth/google/callback?access_token={tokens.access_token}"
    )
    set_refresh_cookie(redirect, tokens)
    return redirect
