import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.user import User
from tests.constants import (
    TEST_EMAIL_ADDRESS,
    TEST_FIRST_NAME,
    TEST_LAST_NAME,
    TEST_USER_ID,
)
from tests.factories import TEST_PASSWORD_HASH


@pytest_asyncio.fixture
async def persisted_user(db_session):
    # Create new User entry to get the id for foreign key on auth session
    test_user = User(
        id=TEST_USER_ID,
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        email=TEST_EMAIL_ADDRESS,
        password_hash=TEST_PASSWORD_HASH,
    )

    db_session.add(test_user)
    await db_session.flush()

    return test_user


@pytest_asyncio.fixture
async def db_session(async_engine):
    async_session_maker = async_sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()
