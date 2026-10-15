import asyncio

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import CheckConstraint, inspect, make_url, text
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


def get_check_constraints(conn, table_name):
    inspector = inspect(conn)
    constraints = inspector.get_check_constraints(table_name)
    return {constraint["name"] for constraint in constraints}


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

    # Test CHECK constraints present
    async with engine.connect() as conn:
        for table_name, table in Base.metadata.tables.items():
            result = await conn.run_sync(get_check_constraints, table_name)
            table_check_constraints = {
                constraint.name
                for constraint in table.constraints
                if isinstance(constraint, CheckConstraint)
            }
            column_check_constraints = {
                constraint.name
                for column in table.columns
                for constraint in column.constraints
                if isinstance(constraint, CheckConstraint)
            }
            check_constraints = table_check_constraints | column_check_constraints

            assert None not in check_constraints, (
                f"Unnamed check constraint in {table_name}"
            )
            assert result == check_constraints, (
                f"Table {table_name} db_constraints: {result} table_constraints: {check_constraints}"
            )

    await engine.dispose()
