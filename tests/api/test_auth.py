import pytest
from fastapi import status

from app.core.exceptions import DuplicateEmailException
from tests.constants import TEST_SESSION_TOKEN, TEST_USER_ID


def valid_register_payload():
    return {
        "first_name": "test_first",
        "last_name": "test_last",
        "email": "test@email.com",
        "password": "Password123",
    }


async def test_register(client, auth_service):
    register_payload = valid_register_payload()
    res = await client.post("/auth/register", json=register_payload)
    body = res.json()
    header = res.headers["set-cookie"].lower()

    auth_service.register.assert_awaited_once_with(**register_payload)
    assert res.status_code == 201
    assert body["user_id"] == str(TEST_USER_ID)
    assert res.cookies["session_token"] == TEST_SESSION_TOKEN
    assert "httponly" in header
    assert "secure" in header
    assert "samesite=strict" in header


async def test_register_duplicate_email(client, auth_service):
    auth_service.register.side_effect = DuplicateEmailException
    register_payload = valid_register_payload()

    res = await client.post("/auth/register", json=register_payload)
    body = res.json()

    auth_service.register.assert_awaited_once_with(**register_payload)
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
    register_payload = valid_register_payload()
    register_payload[bad_field] = value

    res = await client.post("/auth/register", json=register_payload)
    loc = res.json()["detail"][0]["loc"]

    auth_service.register.assert_not_awaited()
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert bad_field in loc
