from datetime import UTC, datetime, timedelta

from fastapi import status
from sqlalchemy import update

from app.core.config import get_settings
from app.core.utils import get_token_hash
from app.models import AuthSession
from tests.constants import TEST_EMAIL_ADDRESS, TEST_FIRST_NAME
from tests.factories import get_login_payload, get_register_payload


async def test_auth_full_lifecycle(client):
    register_payload = get_register_payload()

    res = await client.post("/auth/register", json=register_payload)
    session_token = res.cookies["session_token"]
    user_id = res.json()["user_id"]

    assert res.status_code == status.HTTP_201_CREATED
    assert "session_token" in res.cookies

    res = await client.get("/auth/me")
    body = res.json()

    assert res.status_code == status.HTTP_200_OK
    assert body["user_id"] == user_id
    assert body["first_name"] == TEST_FIRST_NAME
    assert body["email"] == TEST_EMAIL_ADDRESS

    res = await client.post("/auth/logout")
    header = res.headers["set-cookie"].lower()

    assert "session_token" in header
    assert "max-age=0" in header
    assert res.status_code == status.HTTP_204_NO_CONTENT

    # Explicitly set previous cookie to determine cookie was revoked server-side
    client.cookies.set("session_token", session_token)

    res = await client.get("/auth/me")

    assert res.status_code == status.HTTP_401_UNAUTHORIZED


async def test_register_and_login(client):
    register_payload = get_register_payload()

    res = await client.post("/auth/register", json=register_payload)
    user_id = res.json()["user_id"]
    register_token = res.cookies["session_token"]

    assert res.status_code == status.HTTP_201_CREATED
    assert "session_token" in res.cookies

    login_payload = get_login_payload()

    res = await client.post("/auth/login", json=login_payload)
    login_token = res.cookies["session_token"]

    assert res.status_code == status.HTTP_200_OK
    assert res.json()["user_id"] == user_id
    assert register_token != login_token


async def test_register_with_duplicate_email_different_case(client):
    register_payload = get_register_payload()

    res = await client.post("/auth/register", json=register_payload)

    assert res.status_code == status.HTTP_201_CREATED

    register_payload["email"] = TEST_EMAIL_ADDRESS.upper()
    # Send new register request with the same payload as the first
    res = await client.post("/auth/register", json=register_payload)

    assert res.status_code == status.HTTP_409_CONFLICT


async def test_login_with_wrong_email_or_password_returns_same_response(client):
    register_payload = get_register_payload()
    res = await client.post("/auth/register", json=register_payload)

    assert res.status_code == status.HTTP_201_CREATED

    login_payload = get_login_payload()

    # Make a request with wrong email
    req_body_wrong_email = login_payload.copy()
    req_body_wrong_email["email"] = "wrong-email@email.com"

    res1 = await client.post("/auth/login", json=req_body_wrong_email)
    body1 = res1.json()

    # Make a request with wrong password
    req_body_wrong_password = login_payload.copy()
    req_body_wrong_password["password"] = "wrong-password"

    res2 = await client.post("/auth/login", json=req_body_wrong_password)
    body2 = res2.json()

    assert res1.status_code == res2.status_code == status.HTTP_401_UNAUTHORIZED
    assert body1["detail"] == body2["detail"] == "Invalid credentials"
    assert "set-cookie" not in res1.headers
    assert "set-cookie" not in res2.headers


async def test_idle_expired_limit(db_session, client):
    register_payload = get_register_payload()
    res = await client.post("/auth/register", json=register_payload)

    assert res.status_code == status.HTTP_201_CREATED
    session_token_hash = get_token_hash(res.cookies["session_token"])

    # set last_activity_at past the idle session limit
    idle_session_limit = get_settings().session_idle_timeout_seconds
    expired_idle_timestamp = datetime.now(UTC) - timedelta(
        seconds=idle_session_limit + 12
    )
    statement = (
        update(AuthSession)
        .where(AuthSession.session_token_hash == session_token_hash)
        .values(last_activity_at=expired_idle_timestamp)
    )
    await db_session.execute(statement)
    await db_session.flush()

    res = await client.get("/auth/me")

    assert res.status_code == status.HTTP_401_UNAUTHORIZED


async def test_absolute_expired_limit(db_session, client):
    register_payload = get_register_payload()
    res = await client.post("/auth/register", json=register_payload)

    assert res.status_code == status.HTTP_201_CREATED
    session_token_hash = get_token_hash(res.cookies["session_token"])

    # set created_at past the max age limit
    max_session_limit = get_settings().session_max_lifetime_seconds
    expired_absolute_timestamp = datetime.now(UTC) - timedelta(
        seconds=max_session_limit + 25
    )
    statement = (
        update(AuthSession)
        .where(AuthSession.session_token_hash == session_token_hash)
        .values(created_at=expired_absolute_timestamp)
    )
    await db_session.execute(statement)
    await db_session.flush()

    res = await client.get("/auth/me")

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
