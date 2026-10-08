from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import get_db_config


def get_async_engine() -> AsyncEngine:
    return create_async_engine(
        get_db_config().async_database_url,
        echo=get_db_config().DB_ECHO,
        connect_args=get_db_config().connect_args,
        pool_size=10,
        max_overflow=20,
        pool_recycle=300,
        pool_pre_ping=True,
    )

def get_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)