from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_auth_service
from app.main import app
from app.services.auth_service import (
    AuthenticatedUser,
    AuthResult,
    AuthService,
    SessionToken,
    UserInfo,
)
from tests.constants import (
    TEST_EMAIL_ADDRESS,
    TEST_FIRST_NAME,
    TEST_LAST_NAME,
    TEST_MAX_COOKIE_AGE,
    TEST_SESSION_TOKEN,
    TEST_USER_ID,
)


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


@pytest_asyncio.fixture
async def client(auth_service):
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client
    app.dependency_overrides.clear()
