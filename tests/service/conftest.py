from unittest.mock import AsyncMock

import pytest

from app.core.utils import get_password_hash
from app.daos.auth_session_dao import AuthSessionDao
from app.daos.user_dao import UserDao
from app.models import User
from tests.constants import (
    TEST_CREATED_AT,
    TEST_EMAIL_ADDRESS,
    TEST_FIRST_NAME,
    TEST_LAST_ACTIVITY_AT,
    TEST_LAST_NAME,
    TEST_PASSWORD,
    TEST_USER_ID,
)
from tests.factories import make_auth_session

TEST_PASSWORD_HASH = get_password_hash(TEST_PASSWORD)


@pytest.fixture
def auth_session_dao():
    mock_auth_session_dao = AsyncMock(spec=AuthSessionDao)
    mock_auth_session_dao.create_auth_session.return_value = make_auth_session()
    mock_auth_session_dao.get_auth_session_by_hash.return_value = make_auth_session(
        created_at=TEST_CREATED_AT, last_activity_at=TEST_LAST_ACTIVITY_AT
    )
    return mock_auth_session_dao


@pytest.fixture
def user_dao():
    mock_user_dao = AsyncMock(spec=UserDao)
    mock_user = User(
        id=TEST_USER_ID,
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        email=TEST_EMAIL_ADDRESS,
        password_hash=TEST_PASSWORD_HASH,
    )
    mock_user_dao.create_user = AsyncMock(return_value=mock_user)
    return mock_user_dao
