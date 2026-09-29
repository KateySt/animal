from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_async_engine, get_session_factory

engine = get_async_engine()

AsyncSessionLocal = get_session_factory(engine)


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with request.app.state.db_sessionmaker() as session:
        yield session
