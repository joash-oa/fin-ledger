import pytest
import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient, Response

from app.api.deps import get_auth_service
from app.core.exceptions import (
    DuplicateEmailException,
    InvalidCredentialsException,
    UserNotFoundException,
)
from app.main import app
from tests.constants import (
    TEST_EMAIL_ADDRESS,
    TEST_FIRST_NAME,
    TEST_LAST_NAME,
    TEST_SESSION_TOKEN,
    TEST_USER_ID,
)
from tests.factories import get_login_payload, get_register_payload


@pytest_asyncio.fixture
async def client(auth_service):
    # API dependencies
    app.dependency_overrides[get_auth_service] = lambda: auth_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client
    app.dependency_overrides.clear()


def assert_authenticated_response(res: Response, status_code: int):
    body = res.json()
    header = res.headers["set-cookie"].lower()

    assert res.status_code == status_code
    assert body["user_id"] == str(TEST_USER_ID)
    assert res.cookies["session_token"] == TEST_SESSION_TOKEN
    assert "httponly" in header
    assert "secure" in header
    assert "samesite=strict" in header


async def test_register(client, auth_service):
    payload = get_register_payload()
    res = await client.post("/auth/register", json=payload)

    auth_service.register.assert_awaited_once_with(**payload)
    assert_authenticated_response(res, status_code=201)


async def test_register_duplicate_email(client, auth_service):
    payload = get_register_payload()
    auth_service.register.side_effect = DuplicateEmailException
    res = await client.post("/auth/register", json=payload)
    body = res.json()

    auth_service.register.assert_awaited_once_with(**payload)
    assert res.status_code == status.HTTP_409_CONFLICT
    assert body["detail"] == "Email already in use"


@pytest.mark.parametrize(
    "bad_field, value",
    [
        ("first_name", "x" * 51),
        ("last_name", ""),
        ("email", "bad-test-value"),
        ("password", "2short"),
    ],
)
async def test_register_with_invalid_request_body(
    client, auth_service, bad_field, value
):
    payload = get_register_payload()
    payload[bad_field] = value
    res = await client.post("/auth/register", json=payload)
    loc = res.json()["detail"][0]["loc"]

    auth_service.register.assert_not_awaited()
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert bad_field in loc


async def test_login(client, auth_service):
    payload = get_login_payload()
    res = await client.post("/auth/login", json=payload)

    auth_service.login.assert_awaited_once_with(**payload)
    assert_authenticated_response(res, status_code=200)


async def test_login_with_wrong_credentials_return_same_responses(client, auth_service):
    """Test that /login with both wrong password and email returns same response. Proves mapping NOT response logic"""
    payload = get_login_payload()
    auth_service.login.side_effect = InvalidCredentialsException

    # Make a request with wrong email
    req_body_wrong_email = payload.copy()
    req_body_wrong_email["email"] = "test-wrong-email@email.com"

    res1 = await client.post("/auth/login", json=req_body_wrong_email)
    body1 = res1.json()

    # Make a request with wrong password
    req_body_wrong_password = payload.copy()
    req_body_wrong_password["password"] = "test-wrong-password"

    res2 = await client.post("/auth/login", json=req_body_wrong_password)
    body2 = res2.json()

    # Test if login was called with both requests
    auth_service.login.assert_any_await(**req_body_wrong_email)
    auth_service.login.assert_any_await(**req_body_wrong_password)

    # Test if both requests returned the same response (same status codes and details)
    assert res1.status_code == res2.status_code == status.HTTP_401_UNAUTHORIZED
    assert body1["detail"] == body2["detail"] == "Invalid credentials"
    assert "set-cookie" not in res1.headers
    assert "set-cookie" not in res2.headers


async def test_login_with_invalid_email(client, auth_service):
    payload = get_login_payload()
    payload["email"] = "not-an-email"
    res = await client.post("/auth/login", json=payload)
    loc = res.json()["detail"][0]["loc"]

    auth_service.login.assert_not_awaited()
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "email" in loc


async def test_logout(client, auth_service):
    client.cookies.set("session_token", TEST_SESSION_TOKEN)
    res = await client.post("/auth/logout")
    header = res.headers["set-cookie"].lower()

    auth_service.logout.assert_awaited_once_with(TEST_SESSION_TOKEN)
    assert "session_token" in header
    assert "max-age=0" in header
    assert res.status_code == status.HTTP_204_NO_CONTENT


async def test_logout_with_no_session_token(client, auth_service):
    res = await client.post("/auth/logout")

    auth_service.logout.assert_not_awaited()
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


async def test_me_success(client, auth_service):
    client.cookies.set("session_token", TEST_SESSION_TOKEN)
    res = await client.get("/auth/me")
    body = res.json()

    auth_service.authenticate.assert_awaited_once_with(TEST_SESSION_TOKEN)
    auth_service.get_user_by_id.assert_awaited_once_with(TEST_USER_ID)
    assert res.status_code == status.HTTP_200_OK
    assert body["user_id"] == str(TEST_USER_ID)
    assert body["first_name"] == TEST_FIRST_NAME
    assert body["last_name"] == TEST_LAST_NAME
    assert body["email"] == TEST_EMAIL_ADDRESS


async def test_me_with_no_session_token(client, auth_service):
    res = await client.get("/auth/me")

    auth_service.authenticate.assert_not_awaited()
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


async def test_me_with_unknown_user(client, auth_service):
    auth_service.get_user_by_id.side_effect = UserNotFoundException
    client.cookies.set("session_token", TEST_SESSION_TOKEN)

    res = await client.get("/auth/me")

    auth_service.authenticate.assert_awaited_once_with(TEST_SESSION_TOKEN)
    auth_service.get_user_by_id.assert_awaited_once_with(TEST_USER_ID)

    assert res.status_code == status.HTTP_404_NOT_FOUND
