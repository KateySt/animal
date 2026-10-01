from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine

from app.core import get_async_engine


@asynccontextmanager
async def worker_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = get_async_engine()
    try:
        yield engine
    finally:
        await engine.dispose()
