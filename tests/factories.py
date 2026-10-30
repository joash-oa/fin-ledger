from datetime import datetime
from uuid import UUID

from app.core.mapping import AccountMapping
from app.core.utils import get_password_hash, get_token_hash
from app.models import Account, AuthSession, User
from tests.constants import (
    TEST_ACCOUNT_ID,
    TEST_ACCOUNT_INSTITUTION,
    TEST_ACCOUNT_NAME,
    TEST_ACCOUNT_TYPE,
    TEST_AMOUNT,
    TEST_CREATED_AT,
    TEST_DATE_FORMAT,
    TEST_DESCRIPTION,
    TEST_EMAIL_ADDRESS,
    TEST_FIRST_NAME,
    TEST_LAST_NAME,
    TEST_MASKED_NUMBER,
    TEST_NOW,
    TEST_PASSWORD,
    TEST_POSTED_AT,
    TEST_RAW_TYPE,
    TEST_ROW_ORDER,
    TEST_RUNNING_BALANCE,
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


def get_create_account_payload():
    return {
        "account_name": TEST_ACCOUNT_NAME,
        "account_type": TEST_ACCOUNT_TYPE,
        "masked_number": TEST_MASKED_NUMBER,
        "institution": TEST_ACCOUNT_INSTITUTION,
    }


def get_update_account_payload():
    return {
        "mapping": {
            "posted_at": TEST_POSTED_AT,
            "amount": TEST_AMOUNT,
            "description": TEST_DESCRIPTION,
            "running_balance": TEST_RUNNING_BALANCE,
            "raw_type": TEST_RAW_TYPE,
            "date_format": TEST_DATE_FORMAT,
            "row_order": TEST_ROW_ORDER,
        }
    }


def get_mock_account() -> Account:
    return Account(
        id=TEST_ACCOUNT_ID,
        name=TEST_ACCOUNT_NAME,
        user_id=TEST_USER_ID,
        type=TEST_ACCOUNT_TYPE,
        institution=TEST_ACCOUNT_INSTITUTION,
        masked_number=TEST_MASKED_NUMBER,
        created_at=TEST_CREATED_AT,
        mapping=None,
    )


def get_create_account_data():
    return {
        "user_id": TEST_USER_ID,
        "account_name": TEST_ACCOUNT_NAME,
        "account_type": TEST_ACCOUNT_TYPE,
        "masked_number": TEST_MASKED_NUMBER,
        "institution": TEST_ACCOUNT_INSTITUTION,
    }


def get_users_payloads():
    first_user_payload = {
        "first_name": "First",
        "last_name": "Last",
        "email": "first_last@email.com",
        "password": "first-password-123",
    }

    second_user_payload = {
        "first_name": "Second",
        "last_name": "Last",
        "email": "second_last@email.com",
        "password": "second-password-123",
    }

    return [first_user_payload, second_user_payload]


def get_valid_mapping():
    return AccountMapping(
        posted_at="Date",
        amount="Amount",
        description="Description",
        running_balance="Current balance",
        raw_type="Type",
        date_format="YYYY MM DD",
        row_order="asc",
    )


def make_csv_file(
    file_lines: list[str], bom: bool = False, encoding: str = "utf-8"
) -> bytes:
    text = "\n".join(file_lines) + "\n"
    file_bytes = text.encode(encoding)
    if bom:
        file_bytes = b"\xef\xbb\xbf" + file_bytes
    return file_bytes
