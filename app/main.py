from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import stripe
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.admin import setup_admin
from app.core import get_app_config
from app.core.config import get_auth_config, get_stripe_config
from app.core.exceptions import CustomError
from app.routers import v1_router
from app.services.redis_service import redis_service

stripe.api_key = get_stripe_config().STRIPE_SECRET_KEY


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(RedisBackend(redis_service.redis), prefix="fastapi-cache")
    yield
    await redis_service.close()


app = FastAPI(
    title=get_app_config().APP_NAME,
    debug=get_app_config().DEBUG,
    root_path="/api",
    lifespan=lifespan,
)

app.add_middleware(SessionMiddleware, secret_key=get_auth_config().ADMIN_SECRET)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_auth_config().CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_admin(app)


@app.exception_handler(CustomError)
async def app_error_handler(_: Request, error: CustomError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content={"detail": error.detail}, headers=error.headers)


app.include_router(v1_router)
