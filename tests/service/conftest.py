from unittest.mock import AsyncMock

import pytest

from app.daos.account_dao import AccountDao
from app.daos.auth_session_dao import AuthSessionDao
from app.daos.user_dao import UserDao
from tests.constants import (
    TEST_CREATED_AT,
    TEST_LAST_ACTIVITY_AT,
)
from tests.factories import get_mock_account, get_mock_user, make_auth_session


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
    mock_user_dao.get_user_by_id.return_value = get_mock_user()
    return mock_user_dao


@pytest.fixture
def account_dao():
    mock_account_dao = AsyncMock(spec=AccountDao)
    test_account = get_mock_account()
    mock_account_dao.create_account.return_value = test_account
    mock_account_dao.get_account_by_id.return_value = test_account
    mock_account_dao.list_accounts_by_user.return_value = [test_account]
    mock_account_dao.update_mapping.return_value = True

    return mock_account_dao
