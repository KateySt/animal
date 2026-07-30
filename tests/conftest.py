import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_test_config
from app.core.dependencies import get_current_principal, get_db_session
from app.core.security import hash_password
from app.db.models.base import Base
from app.db.models.user import User
from app.main import app
from app.schemas.auth import Principal
from tests.factories import (
    AnimalFactory,
    AnimalTranslationFactory,
    HealthLogFactory,
    HealthLogTranslationFactory,
    UserFactory,
)

_TEST_DB_URL = get_test_config().async_database_url


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def _create_schema():
    engine = create_async_engine(_TEST_DB_URL, poolclass=NullPool, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_db_engine(_create_schema):
    engine = create_async_engine(_TEST_DB_URL, poolclass=NullPool, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_db_engine) -> AsyncGenerator[AsyncSession, None]:
    async with async_db_engine.connect() as conn:
        outer_tx = await conn.begin()

        session = AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")

        sync_session = session.sync_session

        @event.listens_for(sync_session, "after_transaction_end")
        def _restart_savepoint(sess, trans):
            if trans.nested and not trans._parent.nested:
                sess.begin_nested()

        try:
            yield session
        finally:
            event.remove(sync_session, "after_transaction_end", _restart_savepoint)
            await session.close()
            if outer_tx.is_active:
                await outer_tx.rollback()


@pytest.fixture()
def bind_factories(db_session: AsyncSession):
    UserFactory._meta.sqlalchemy_session = db_session
    AnimalFactory._meta.sqlalchemy_session = db_session
    AnimalTranslationFactory._meta.sqlalchemy_session = db_session
    HealthLogFactory._meta.sqlalchemy_session = db_session
    HealthLogTranslationFactory._meta.sqlalchemy_session = db_session


def _db_override(session: AsyncSession):
    def _override():
        yield session

    return _override


def _principal_override(principal: Principal):
    async def _override():
        return principal

    return _override


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db_session] = _db_override(db_session)
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"user_{uuid.uuid4().hex[:8]}@test.com",
        hashed_password=hash_password("TestPass123!"),
        is_active=True,
        is_superuser=True,
        is_verified=True,
        permissions_version=1,
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest_asyncio.fixture
async def auth_client(db_session: AsyncSession, user: User) -> AsyncGenerator[AsyncClient, None]:
    principal = Principal(
        user_id=user.id,
        is_superuser=False,
        scopes=["animals:read", "animals:create", "animals:update", "animals:delete"],
    )
    app.dependency_overrides[get_db_session] = _db_override(db_session)
    app.dependency_overrides[get_current_principal] = _principal_override(principal)
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def superuser_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    principal = Principal(user_id=uuid.uuid4(), is_superuser=True, scopes=[])
    app.dependency_overrides[get_db_session] = _db_override(db_session)
    app.dependency_overrides[get_current_principal] = _principal_override(principal)
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def read_only_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    principal = Principal(user_id=uuid.uuid4(), is_superuser=False, scopes=["animals:read"])
    app.dependency_overrides[get_db_session] = _db_override(db_session)
    app.dependency_overrides[get_current_principal] = _principal_override(principal)
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()
