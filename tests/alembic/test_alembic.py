import asyncio

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import create_async_engine

import app.models  # noqa: F401
from app.core.db import Base


@pytest.fixture(scope="module")
async def migrations_database_url(db_url):
    engine = create_async_engine(db_url, isolation_level="AUTOCOMMIT")

    db_name = "fin_ledger_test_migrations"
    async with engine.connect() as conn:
        await conn.execute(text(f"CREATE DATABASE {db_name}"))

    url = make_url(db_url).set(database=db_name).render_as_string(hide_password=False)
    yield url
    await engine.dispose()


def get_context_diff(conn):
    context = MigrationContext.configure(conn)
    return compare_metadata(context, Base.metadata)


async def test_run_migrations(migrations_database_url):
    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", migrations_database_url)
    await asyncio.to_thread(command.upgrade, alembic_config, "head")

    engine = create_async_engine(migrations_database_url)
    async with engine.connect() as conn:
        result = await conn.run_sync(get_context_diff)
        assert result == []

    await asyncio.to_thread(command.downgrade, alembic_config, "base")
    await asyncio.to_thread(command.upgrade, alembic_config, "head")

    async with engine.connect() as conn:
        result = await conn.run_sync(get_context_diff)
        assert result == []

    await engine.dispose()
