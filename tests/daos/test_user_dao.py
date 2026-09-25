import pytest
from sqlalchemy.exc import IntegrityError

from app.daos.user_dao import UserDao
from app.models import User
from tests.constants import (
    TEST_EMAIL_ADDRESS,
    TEST_FIRST_NAME,
    TEST_LAST_NAME,
    TEST_USER_ID,
)
from tests.factories import TEST_PASSWORD_HASH


async def test_create_user(db_session):
    user_dao = UserDao(db_session)

    user = await user_dao.create_user(
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        email=TEST_LAST_NAME,
        password_hash=TEST_PASSWORD_HASH,
    )

    assert isinstance(user, User)
    assert user.first_name == TEST_FIRST_NAME
    assert user.last_name == TEST_LAST_NAME
    assert user.email == TEST_LAST_NAME
    assert user.password_hash == TEST_PASSWORD_HASH
    assert user.created_at.tzinfo is not None


async def test_create_user_with_duplicate_email_different_case(
    db_session, persisted_user
):
    user_dao = UserDao(db_session)
    duplicate_email = (
        "Test_email@email.com"  # Same email as TEST_EMAIL_ADDRESS in a different case
    )

    with pytest.raises(IntegrityError):
        await user_dao.create_user(
            first_name=TEST_FIRST_NAME,
            last_name=TEST_LAST_NAME,
            email=duplicate_email,
            password_hash=TEST_PASSWORD_HASH,
        )


async def test_get_user_by_email(db_session, persisted_user):
    user_dao = UserDao(db_session)

    user = await user_dao.get_user_by_email(TEST_EMAIL_ADDRESS)

    assert isinstance(user, User)
    assert user.id == persisted_user.id


async def test_get_user_by_email_with_unknown_email(db_session):
    user_dao = UserDao(db_session)

    # No entry in user db
    user = await user_dao.get_user_by_email(TEST_EMAIL_ADDRESS)

    assert user is None


async def test_get_user_by_id(db_session, persisted_user):
    user_dao = UserDao(db_session)

    user = await user_dao.get_user_by_id(TEST_USER_ID)

    assert isinstance(user, User)
    assert user.id == persisted_user.id


async def test_get_user_by_id_with_unknown_id(db_session):
    user_dao = UserDao(db_session)

    # No entry in user db
    user = await user_dao.get_user_by_id(TEST_USER_ID)

    assert user is None
