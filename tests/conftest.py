import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.community.postgres import PostgresContainer

import app.models  # noqa: F401
from app.core.db import Base


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer(image="postgres:18", driver="asyncpg") as pg:
        yield pg


@pytest.fixture(scope="session")
def db_url(postgres_container):
    return postgres_container.get_connection_url()


@pytest_asyncio.fixture(scope="session")
async def async_engine(db_url):
    engine = create_async_engine(db_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()
