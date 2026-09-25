from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from app.core.config import get_settings
from app.core.exceptions import (
    DuplicateEmailException,
    InvalidCredentialsException,
    InvalidSessionException,
    UserNotFoundException,
)
from app.core.utils import get_token_hash, verify_password
from app.services.auth_service import DUMMY_PASSWORD_HASH, AuthService
from tests.constants import (
    TEST_CREATED_AT,
    TEST_EMAIL_ADDRESS,
    TEST_FIRST_NAME,
    TEST_LAST_ACTIVITY_AT,
    TEST_LAST_NAME,
    TEST_NOW,
    TEST_PASSWORD,
    TEST_SESSION_TOKEN,
    TEST_USER_ID,
)
from tests.factories import (
    get_auth_service_register_data,
    get_mock_user,
    make_auth_session,
)


@pytest.fixture
def auth_service(auth_session_dao, user_dao) -> AuthService:
    return AuthService(
        auth_session_dao=auth_session_dao, user_dao=user_dao, now=lambda: TEST_NOW
    )


async def test_register_success(auth_service, auth_session_dao, user_dao):
    register_data = get_auth_service_register_data()
    user_dao.get_user_by_email.return_value = None

    auth_result = await auth_service.register(**register_data)

    user_id = auth_result.user_id
    session_token = auth_result.session_token
    create_auth_session_args = auth_session_dao.create_auth_session.call_args.kwargs
    create_user_args = user_dao.create_user.call_args.kwargs

    user_dao.get_user_by_email.assert_awaited_once_with(TEST_EMAIL_ADDRESS)
    user_dao.create_user.assert_awaited_once()
    assert verify_password(TEST_PASSWORD, create_user_args["password_hash"])

    auth_session_dao.create_auth_session.assert_awaited_once()
    assert (
        get_token_hash(session_token.value)
        == create_auth_session_args["session_token_hash"]
    )
    assert TEST_USER_ID == create_auth_session_args["user_id"]
    assert user_id == TEST_USER_ID


async def test_register_with_duplicate_email(auth_service, auth_session_dao, user_dao):
    register_data = get_auth_service_register_data()
    user_dao.get_user_by_email.return_value = get_mock_user()

    with pytest.raises(DuplicateEmailException):
        await auth_service.register(**register_data)

    user_dao.get_user_by_email.assert_awaited_once_with(TEST_EMAIL_ADDRESS)
    user_dao.create_user.assert_not_awaited()

    auth_session_dao.create_auth_session.assert_not_awaited()


async def test_login_success(auth_service, auth_session_dao, user_dao):
    user_dao.get_user_by_email.return_value = get_mock_user()

    auth_result = await auth_service.login(TEST_EMAIL_ADDRESS, TEST_PASSWORD)
    user_id = auth_result.user_id
    session_token = auth_result.session_token
    create_auth_session_args = auth_session_dao.create_auth_session.call_args.kwargs

    user_dao.get_user_by_email.assert_awaited_once_with(TEST_EMAIL_ADDRESS)
    assert (
        get_token_hash(session_token.value)
        == create_auth_session_args["session_token_hash"]
    )
    assert TEST_USER_ID == create_auth_session_args["user_id"]
    assert session_token.max_age == get_settings().session_max_lifetime_seconds
    assert user_id == TEST_USER_ID


async def test_login_with_wrong_password(auth_service, auth_session_dao, user_dao):
    user_dao.get_user_by_email.return_value = get_mock_user()

    with pytest.raises(InvalidCredentialsException):
        await auth_service.login(email=TEST_EMAIL_ADDRESS, password="wrong_password")

    user_dao.get_user_by_email.assert_awaited_once_with(TEST_EMAIL_ADDRESS)
    auth_session_dao.create_auth_session.assert_not_awaited()


async def test_login_with_wrong_email(
    auth_service, auth_session_dao, user_dao, monkeypatch
):
    spy = MagicMock(wraps=verify_password)
    monkeypatch.setattr("app.services.auth_service.verify_password", spy)
    user_dao.get_user_by_email.return_value = None

    with pytest.raises(InvalidCredentialsException):
        await auth_service.login(email="wrong-email", password=TEST_PASSWORD)

    spy.assert_called_once_with(TEST_PASSWORD, DUMMY_PASSWORD_HASH)
    user_dao.get_user_by_email.assert_awaited_once_with("wrong-email")
    auth_session_dao.create_auth_session.assert_not_awaited()


async def test_authenticate_success(auth_service, auth_session_dao):
    authenticated_user = await auth_service.authenticate(TEST_SESSION_TOKEN)

    assert authenticated_user.user_id == TEST_USER_ID
    auth_session_dao.get_auth_session_by_hash.assert_awaited_once_with(
        get_token_hash(TEST_SESSION_TOKEN)
    )
    auth_session_dao.update_last_activity.assert_awaited_once_with(
        session_token_hash=get_token_hash(TEST_SESSION_TOKEN), timestamp=TEST_NOW
    )


async def test_authenticate_with_unknown_token(auth_service, auth_session_dao):
    auth_session_dao.get_auth_session_by_hash.return_value = None
    unknown_token = "some_unknown_token"

    with pytest.raises(InvalidSessionException):
        await auth_service.authenticate(unknown_token)

    auth_session_dao.get_auth_session_by_hash.assert_awaited_once_with(
        get_token_hash(unknown_token)
    )
    auth_session_dao.update_last_activity.assert_not_awaited()


async def test_authenticate_with_idle_expired_token(auth_service, auth_session_dao):
    idle_time_limit = get_settings().session_idle_timeout_seconds
    auth_session_dao.get_auth_session_by_hash.return_value = make_auth_session(
        created_at=TEST_CREATED_AT,
        last_activity_at=TEST_NOW - timedelta(seconds=idle_time_limit + 10),
    )
    with pytest.raises(InvalidSessionException):
        await auth_service.authenticate(TEST_SESSION_TOKEN)

    auth_session_dao.get_auth_session_by_hash.assert_awaited_once_with(
        get_token_hash(TEST_SESSION_TOKEN)
    )
    auth_session_dao.update_last_activity.assert_not_awaited()


async def test_authenticate_with_idle_expired_at_boundary(
    auth_service, auth_session_dao
):
    idle_time_limit = get_settings().session_idle_timeout_seconds
    auth_session_dao.get_auth_session_by_hash.return_value = make_auth_session(
        created_at=TEST_CREATED_AT,
        last_activity_at=TEST_NOW - timedelta(seconds=idle_time_limit),
    )
    with pytest.raises(InvalidSessionException):
        await auth_service.authenticate(TEST_SESSION_TOKEN)

    auth_session_dao.get_auth_session_by_hash.assert_awaited_once_with(
        get_token_hash(TEST_SESSION_TOKEN)
    )
    auth_session_dao.update_last_activity.assert_not_awaited()


async def test_authenticate_with_absolute_expired_token(auth_service, auth_session_dao):
    absolute_time_limit = get_settings().session_max_lifetime_seconds
    auth_session_dao.get_auth_session_by_hash.return_value = make_auth_session(
        created_at=TEST_NOW - timedelta(seconds=absolute_time_limit + 10),
        last_activity_at=TEST_LAST_ACTIVITY_AT,
    )
    with pytest.raises(InvalidSessionException):
        await auth_service.authenticate(TEST_SESSION_TOKEN)

    auth_session_dao.get_auth_session_by_hash.assert_awaited_once_with(
        get_token_hash(TEST_SESSION_TOKEN)
    )
    auth_session_dao.update_last_activity.assert_not_awaited()


async def test_authenticate_with_absolute_expired_at_boundary(
    auth_service, auth_session_dao
):
    absolute_time_limit = get_settings().session_max_lifetime_seconds
    auth_session_dao.get_auth_session_by_hash.return_value = make_auth_session(
        created_at=TEST_NOW - timedelta(seconds=absolute_time_limit),
        last_activity_at=TEST_LAST_ACTIVITY_AT,
    )
    with pytest.raises(InvalidSessionException):
        await auth_service.authenticate(TEST_SESSION_TOKEN)

    auth_session_dao.get_auth_session_by_hash.assert_awaited_once_with(
        get_token_hash(TEST_SESSION_TOKEN)
    )
    auth_session_dao.update_last_activity.assert_not_awaited()


async def test_logout(auth_service, auth_session_dao):
    await auth_service.logout(TEST_SESSION_TOKEN)

    auth_session_dao.delete_auth_session.assert_awaited_once_with(
        get_token_hash(TEST_SESSION_TOKEN)
    )


async def test_get_user_by_id(auth_service, user_dao):
    user = await auth_service.get_user_by_id(TEST_USER_ID)

    user_dao.get_user_by_id.assert_awaited_once_with(TEST_USER_ID)
    assert user.user_id == TEST_USER_ID
    assert user.first_name == TEST_FIRST_NAME
    assert user.last_name == TEST_LAST_NAME
    assert user.email == TEST_EMAIL_ADDRESS


async def test_get_user_by_id_with_unknown_id(auth_service, user_dao):
    user_dao.get_user_by_id.return_value = None

    with pytest.raises(UserNotFoundException):
        await auth_service.get_user_by_id(TEST_USER_ID)
