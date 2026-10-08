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
from app.core.blob import documents_storage, public_storage
from app.core.book_rag.client import close_client as close_book_rag_client
from app.core.config import get_auth_config, get_stripe_config
from app.core.exceptions import CustomError
from app.core.middleware import UnhandledErrorMiddleware
from app.db.session import AsyncSessionLocal, engine
from app.routers import v1_router
from app.services.redis_service import redis_service

stripe.api_key = get_stripe_config().STRIPE_SECRET_KEY


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.db_engine = engine
    app.state.db_sessionmaker = AsyncSessionLocal
    FastAPICache.init(RedisBackend(redis_service.redis), prefix="fastapi-cache")
    yield
    await public_storage.close()
    await documents_storage.close()
    await close_book_rag_client()
    await redis_service.close()
    await engine.dispose()


app = FastAPI(
    title=get_app_config().APP_NAME,
    debug=get_app_config().DEBUG,
    lifespan=lifespan,
)

app.add_middleware(UnhandledErrorMiddleware)

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
    content: dict = {"detail": error.detail}
    if error.error_code is not None:
        content["error_code"] = error.error_code
    return JSONResponse(status_code=error.status_code, content=content, headers=error.headers)


app.include_router(v1_router, prefix="/api")
