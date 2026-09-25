import pytest_asyncio

from app.core.utils import get_token_hash
from app.daos.auth_session_dao import AuthSessionDao
from app.models import AuthSession
from tests.constants import TEST_LAST_ACTIVITY_AT, TEST_SESSION_TOKEN


@pytest_asyncio.fixture
async def created_auth_session(db_session, persisted_user) -> AuthSession:
    auth_session_dao = AuthSessionDao(db_session)
    auth_session = await auth_session_dao.create_auth_session(
        session_token_hash=get_token_hash(TEST_SESSION_TOKEN), user_id=persisted_user.id
    )
    return auth_session


async def test_create_auth_session(db_session, persisted_user):
    auth_session_dao = AuthSessionDao(db_session)

    session_token_hash = get_token_hash(TEST_SESSION_TOKEN)
    auth_session = await auth_session_dao.create_auth_session(
        session_token_hash=session_token_hash, user_id=persisted_user.id
    )

    assert isinstance(auth_session, AuthSession)
    assert auth_session.user_id == persisted_user.id
    assert auth_session.session_token_hash == get_token_hash(TEST_SESSION_TOKEN)
    assert auth_session.created_at.tzinfo is not None
    assert auth_session.last_activity_at.tzinfo is not None
    assert auth_session.created_at == auth_session.last_activity_at


async def test_get_auth_session_by_hash(created_auth_session, db_session):
    auth_session_dao = AuthSessionDao(db_session)
    session_token_hash = get_token_hash(TEST_SESSION_TOKEN)

    auth_session = await auth_session_dao.get_auth_session_by_hash(session_token_hash)

    assert isinstance(auth_session, AuthSession)
    assert auth_session.id == created_auth_session.id
    assert auth_session.session_token_hash == session_token_hash


async def test_get_auth_session_by_hash_with_unknown_hash(db_session):
    auth_session_dao = AuthSessionDao(db_session)
    session_token_hash = get_token_hash(TEST_SESSION_TOKEN)

    # No auth_session in db
    auth_session = await auth_session_dao.get_auth_session_by_hash(session_token_hash)

    assert auth_session is None


async def test_update_last_activity(created_auth_session, db_session):
    auth_session_dao = AuthSessionDao(db_session)

    await auth_session_dao.update_last_activity(
        session_token_hash=created_auth_session.session_token_hash,
        timestamp=TEST_LAST_ACTIVITY_AT,
    )
    # refresh the session to avoid reading from cached identity map. see: https://stackoverflow.com/questions/77928996/how-to-force-sqlalchemy-to-make-a-fresh-select-from-the-database-instead-of-reus
    await db_session.refresh(created_auth_session)

    assert created_auth_session.last_activity_at == TEST_LAST_ACTIVITY_AT


async def test_delete_auth_session(created_auth_session, db_session):
    auth_session_dao = AuthSessionDao(db_session)
    session_token_hash = get_token_hash(TEST_SESSION_TOKEN)

    await auth_session_dao.delete_auth_session(created_auth_session.session_token_hash)
    auth_session = await auth_session_dao.get_auth_session_by_hash(session_token_hash)

    assert auth_session is None


async def test_delete_auth_session_with_unknown_hash(db_session):
    # Test that deleting an auth session with an unknown hash in the db does not raise
    auth_session_dao = AuthSessionDao(db_session)
    session_token_hash = get_token_hash(TEST_SESSION_TOKEN)

    await auth_session_dao.delete_auth_session(session_token_hash=session_token_hash)
