from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.middleware.cors import CORSMiddleware

from app.admin import setup_admin
from app.core import app_config
from app.core.config import auth_config
from app.core.exceptions import CustomError
from app.services.user_manager import fastapi_users
from app.core.google_oauth import google_oauth_client
from app.routers import animal_router, health_log_router, policy_router
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.redis_service import redis_service
from app.services.user_manager import auth_backend


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(RedisBackend(redis_service.redis), prefix="fastapi-cache")
    yield
    await redis_service.close()


app = FastAPI(
    title=app_config.APP_NAME,
    debug=app_config.DEBUG,
    root_path="/api",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_admin(app)


@app.exception_handler(CustomError)
async def app_error_handler(_: Request, error: CustomError):
    return JSONResponse(status_code=error.status_code, content={"detail": error.detail})


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_oauth_router(
        google_oauth_client,
        auth_backend,
        auth_config.ACCESS_TOKEN_SECRET,
        redirect_url=auth_config.GOOGLE_REDIRECT_URI,
        associate_by_email=True,
        is_verified_by_default=True,
    ),
    prefix="/auth/google",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["Users"],
)
app.include_router(animal_router, prefix="/animals", tags=["Animals"])
app.include_router(health_log_router, prefix="/animals/{animal_id}/health-logs", tags=["Health Logs"])
app.include_router(policy_router, prefix="/permissions", tags=["Permissions"])
