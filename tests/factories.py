from datetime import datetime
from uuid import UUID

from app.core.utils import get_password_hash, get_token_hash
from app.models import AuthSession, User
from tests.constants import (
    TEST_EMAIL_ADDRESS,
    TEST_FIRST_NAME,
    TEST_LAST_NAME,
    TEST_NOW,
    TEST_PASSWORD,
    TEST_SESSION_ID,
    TEST_SESSION_TOKEN,
    TEST_USER_ID,
)

TEST_PASSWORD_HASH = get_password_hash(TEST_PASSWORD)


def make_auth_session(
    session_id: UUID = TEST_SESSION_ID,
    session_token: str = TEST_SESSION_TOKEN,
    user_id: UUID = TEST_USER_ID,
    created_at: datetime = TEST_NOW,
    last_activity_at: datetime = TEST_NOW,
) -> AuthSession:
    mock_auth_session = AuthSession(
        id=session_id,
        session_token_hash=get_token_hash(session_token),
        user_id=user_id,
        created_at=created_at,
        last_activity_at=last_activity_at,
    )
    return mock_auth_session


def get_auth_service_register_data() -> dict[str, str]:
    return {
        "first_name": TEST_FIRST_NAME,
        "last_name": TEST_LAST_NAME,
        "email": TEST_EMAIL_ADDRESS,
        "password": TEST_PASSWORD,
    }


def get_mock_user() -> User:
    return User(
        id=TEST_USER_ID,
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        email=TEST_EMAIL_ADDRESS,
        password_hash=TEST_PASSWORD_HASH,
        created_at=TEST_NOW,
    )


def get_login_payload():
    return {
        "email": TEST_EMAIL_ADDRESS,
        "password": TEST_PASSWORD,
    }


def get_register_payload():
    return {
        "first_name": TEST_FIRST_NAME,
        "last_name": TEST_LAST_NAME,
        "email": TEST_EMAIL_ADDRESS,
        "password": TEST_PASSWORD,
    }
