from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.middleware.cors import CORSMiddleware

from app.admin import setup_admin
from app.core import app_config
from app.core.exceptions import CustomError
from app.routers import animal_router, auth_router, health_log_router
from app.services import redis_service


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


app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(animal_router, prefix="/animals", tags=["Animals"])
app.include_router(health_log_router, prefix="/animals/{animal_id}/health-logs", tags=["Health Logs"])
