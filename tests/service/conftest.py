from unittest.mock import AsyncMock

import pytest

from app.daos.auth_session_dao import AuthSessionDao
from app.daos.user_dao import UserDao
from tests.constants import (
    TEST_CREATED_AT,
    TEST_LAST_ACTIVITY_AT,
)
from tests.factories import get_mock_user, make_auth_session


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
    mock_user_dao.create_user.return_value = get_mock_user()
    return mock_user_dao
