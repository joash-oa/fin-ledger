from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_auth_service
from app.main import app
from app.services.auth_service import AuthResult, AuthService, SessionToken
from tests.constants import TEST_MAX_LIFETIME_SECONDS, TEST_SESSION_TOKEN, TEST_USER_ID


@pytest.fixture
def auth_service():
    mock_auth_service = AsyncMock(spec=AuthService)
    mock_auth_result = AuthResult(
        user_id=TEST_USER_ID,
        session_token=SessionToken(
            value=TEST_SESSION_TOKEN,
            max_age=TEST_MAX_LIFETIME_SECONDS,
        ),
    )
    mock_auth_service.register = AsyncMock(return_value=mock_auth_result)
    mock_auth_service.login = AsyncMock(return_value=mock_auth_result)
    mock_auth_service.logout = AsyncMock()

    return mock_auth_service


@pytest_asyncio.fixture
async def client(auth_service):
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client
    app.dependency_overrides.clear()
