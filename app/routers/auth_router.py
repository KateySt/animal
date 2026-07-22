from fastapi import APIRouter, Depends, status, Cookie
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse
from app.services import get_user_service
from app.services.user_service import UserService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.register(payload)


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
) -> TokenResponse:
    return await service.login(UserLogin(email=form.username, password=form.password))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token: str = Cookie(...),
    service: UserService = Depends(get_user_service),
) -> TokenResponse:
    return await service.refresh(refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.get_by_email(user.email)
