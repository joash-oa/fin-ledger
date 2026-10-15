import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import get_db_session
from app.main import app


@pytest_asyncio.fixture
async def db_session(async_engine):
    async with async_engine.connect() as conn:
        transaction = await conn.begin()
        async_session_maker = async_sessionmaker(
            bind=conn,
            expire_on_commit=False,
            class_=AsyncSession,
            join_transaction_mode="create_savepoint",
        )
        async with async_session_maker() as session:
            yield session
            await session.rollback()
        await transaction.rollback()


@pytest_asyncio.fixture
async def test_db_session(db_session):
    async def get_test_db_session():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    return get_test_db_session


@pytest_asyncio.fixture
async def client(test_db_session):
    app.dependency_overrides[get_db_session] = test_db_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test"
    ) as async_client:
        yield async_client
    app.dependency_overrides.clear()
