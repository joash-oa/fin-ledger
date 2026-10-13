from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_account_service, get_current_user
from app.main import app
from app.services.account_service import AccountInfo, AccountService, UserAccounts
from app.services.auth_service import (
    AuthenticatedUser,
    AuthResult,
    AuthService,
    SessionToken,
    UserInfo,
)
from tests.constants import (
    TEST_ACCOUNT_ID,
    TEST_ACCOUNT_INSTITUTION,
    TEST_ACCOUNT_NAME,
    TEST_ACCOUNT_TYPE,
    TEST_EMAIL_ADDRESS,
    TEST_FIRST_NAME,
    TEST_LAST_NAME,
    TEST_MASKED_NUMBER,
    TEST_MAX_COOKIE_AGE,
    TEST_SESSION_TOKEN,
    TEST_USER_ID,
)


@pytest.fixture
def current_user():
    return AuthenticatedUser(user_id=TEST_USER_ID)


@pytest.fixture
def auth_service():
    mock_auth_service = AsyncMock(spec=AuthService)
    mock_authenticated_user = AuthenticatedUser(user_id=TEST_USER_ID)
    mock_auth_result = AuthResult(
        user_id=TEST_USER_ID,
        session_token=SessionToken(
            value=TEST_SESSION_TOKEN,
            max_age=TEST_MAX_COOKIE_AGE,
        ),
    )
    mock_user_info = UserInfo(
        user_id=TEST_USER_ID,
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        email=TEST_EMAIL_ADDRESS,
    )

    mock_auth_service.register.return_value = mock_auth_result
    mock_auth_service.login.return_value = mock_auth_result
    mock_auth_service.logout.return_value = None
    mock_auth_service.authenticate.return_value = mock_authenticated_user
    mock_auth_service.get_user_by_id.return_value = mock_user_info

    return mock_auth_service


@pytest.fixture
def account_service():
    mock_account_service = AsyncMock(spec=AccountService)
    mock_account_info = AccountInfo(
        account_id=TEST_ACCOUNT_ID,
        account_name=TEST_ACCOUNT_NAME,
        institution=TEST_ACCOUNT_INSTITUTION,
        account_type=TEST_ACCOUNT_TYPE,
        masked_number=TEST_MASKED_NUMBER,
        balance=None,
        mapping=None,
    )
    mock_account_service.create_account.return_value = TEST_ACCOUNT_ID
    mock_account_service.get_account_by_id.return_value = mock_account_info
    mock_account_service.update_account_mapping.return_value = None
    mock_account_service.list_accounts.return_value = UserAccounts(
        accounts=[mock_account_info],
        net_balance=None,
    )

    return mock_account_service


@pytest_asyncio.fixture
async def client(account_service, current_user):
    # API dependencies
    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_account_service] = lambda: account_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client
    app.dependency_overrides.clear()
