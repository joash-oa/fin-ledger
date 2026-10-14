import uuid

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import DuplicateAccountException
from app.daos.account_dao import AccountDao
from app.models import Account, User
from tests.constants import (
    TEST_ACCOUNT_ID,
    TEST_ACCOUNT_INSTITUTION,
    TEST_ACCOUNT_NAME,
    TEST_ACCOUNT_TYPE,
    TEST_MASKED_NUMBER,
)
from tests.factories import TEST_PASSWORD_HASH, get_update_account_payload


@pytest_asyncio.fixture
async def created_account(db_session, persisted_user):
    account_dao = AccountDao(db_session)
    account = await account_dao.create_account(
        user_id=persisted_user.id,
        account_name=TEST_ACCOUNT_NAME,
        account_type=TEST_ACCOUNT_TYPE,
        institution=TEST_ACCOUNT_INSTITUTION,
        masked_number=TEST_MASKED_NUMBER,
    )
    return account


@pytest_asyncio.fixture
async def second_persisted_user(db_session):
    user = User(
        first_name="Second",
        last_name="User",
        email="second_user@email.com",
        password_hash=TEST_PASSWORD_HASH,
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def test_create_account(db_session, persisted_user):
    account_dao = AccountDao(db_session)

    account = await account_dao.create_account(
        user_id=persisted_user.id,
        account_name=TEST_ACCOUNT_NAME,
        account_type=TEST_ACCOUNT_TYPE,
        institution=TEST_ACCOUNT_INSTITUTION,
        masked_number=TEST_MASKED_NUMBER,
    )

    assert isinstance(account, Account)
    assert account.user_id == persisted_user.id
    assert account.name == TEST_ACCOUNT_NAME
    assert account.institution == TEST_ACCOUNT_INSTITUTION
    assert account.masked_number == TEST_MASKED_NUMBER
    assert account.type == TEST_ACCOUNT_TYPE
    assert account.mapping is None


async def test_create_account_duplicate_account(
    db_session, persisted_user, created_account
):
    account_dao = AccountDao(db_session)

    # same user_id, type, masked_number, institution defies ux_account constraint on accounts table
    # should raise Integrity Error which we catch and re-raise as a DuplicateAccountException
    with pytest.raises(DuplicateAccountException):
        await account_dao.create_account(
            user_id=persisted_user.id,
            account_name=TEST_ACCOUNT_NAME,
            account_type=TEST_ACCOUNT_TYPE,
            institution=TEST_ACCOUNT_INSTITUTION,
            masked_number=TEST_MASKED_NUMBER,
        )


async def test_create_account_with_different_user_duplicate_info(
    db_session, created_account, second_persisted_user
):
    account_dao = AccountDao(db_session)

    # same type, masked_number, institution but with different user_id, works
    account = await account_dao.create_account(
        user_id=second_persisted_user.id,
        account_name=TEST_ACCOUNT_NAME,
        account_type=TEST_ACCOUNT_TYPE,
        institution=TEST_ACCOUNT_INSTITUTION,
        masked_number=TEST_MASKED_NUMBER,
    )

    assert isinstance(account, Account)
    assert account.user_id == second_persisted_user.id
    assert account.name == TEST_ACCOUNT_NAME
    assert account.institution == TEST_ACCOUNT_INSTITUTION
    assert account.masked_number == TEST_MASKED_NUMBER
    assert account.type == TEST_ACCOUNT_TYPE
    assert account.mapping is None


async def test_create_account_with_non_existent_user(db_session):
    account_dao = AccountDao(db_session)
    non_existent_user_id = uuid.uuid4()

    # non-existent user raises IntegrityError
    with pytest.raises(IntegrityError):
        await account_dao.create_account(
            user_id=non_existent_user_id,
            account_name=TEST_ACCOUNT_NAME,
            account_type=TEST_ACCOUNT_TYPE,
            institution=TEST_ACCOUNT_INSTITUTION,
            masked_number=TEST_MASKED_NUMBER,
        )


async def test_create_account_with_unallowed_type(db_session, persisted_user):
    account_dao = AccountDao(db_session)

    # CHECK constraint forces IntegrityError for type = "credit"
    with pytest.raises(IntegrityError):
        await account_dao.create_account(
            user_id=persisted_user.id,
            account_name=TEST_ACCOUNT_NAME,
            account_type="credit",
            institution=TEST_ACCOUNT_INSTITUTION,
            masked_number=TEST_MASKED_NUMBER,
        )


async def test_get_account_by_id(created_account, db_session, persisted_user):
    account_dao = AccountDao(db_session)

    account = await account_dao.get_account_by_id(
        user_id=persisted_user.id,
        account_id=created_account.id,
    )

    assert isinstance(account, Account)
    assert account.user_id == persisted_user.id
    assert account.id == created_account.id
    assert account.institution == created_account.institution
    assert account.mapping is None


async def test_get_account_with_non_existent_account(db_session, persisted_user):
    account_dao = AccountDao(db_session)

    # no account in db
    account = await account_dao.get_account_by_id(
        user_id=persisted_user.id, account_id=TEST_ACCOUNT_ID
    )

    assert account is None


async def test_get_account_with_wrong_user(
    db_session, created_account, second_persisted_user
):
    account_dao = AccountDao(db_session)

    # Should return None for wrong user ID
    account = await account_dao.get_account_by_id(
        account_id=created_account.id, user_id=second_persisted_user.id
    )

    assert account is None


async def test_list_accounts_by_user(created_account, db_session, persisted_user):
    account_dao = AccountDao(db_session)

    accounts = await account_dao.list_accounts_by_user(persisted_user.id)

    assert len(accounts) == 1
    assert all(isinstance(account, Account) for account in accounts)
    assert accounts[0].user_id == persisted_user.id
    assert accounts[0].id == created_account.id


async def test_list_accounts_returned_in_order(db_session, persisted_user):
    account_dao = AccountDao(db_session)

    # Create first account
    first_account = await account_dao.create_account(
        user_id=persisted_user.id,
        account_name="first_account",
        account_type="checking",
        institution="first_account_institution",
        masked_number="0001",
    )

    # Create second account
    second_account = await account_dao.create_account(
        user_id=persisted_user.id,
        account_name="second_account",
        account_type="savings",
        institution="second_account_institution",
        masked_number="0002",
    )

    accounts = await account_dao.list_accounts_by_user(persisted_user.id)

    assert len(accounts) == 2
    assert accounts[0].user_id == accounts[1].user_id == persisted_user.id
    assert accounts[0].id == first_account.id
    assert accounts[1].id == second_account.id


async def test_list_accounts_by_user_with_no_accounts(db_session, persisted_user):
    account_dao = AccountDao(db_session)

    accounts = await account_dao.list_accounts_by_user(persisted_user.id)

    assert len(accounts) == 0


async def test_list_accounts_by_user_excludes_different_user_accounts(
    db_session, persisted_user, second_persisted_user
):
    account_dao = AccountDao(db_session)

    # Create first account
    first_account = await account_dao.create_account(
        user_id=persisted_user.id,
        account_name="first_account",
        account_type="checking",
        institution="first_account_institution",
        masked_number="0001",
    )

    # Create second account with different user
    second_account = await account_dao.create_account(
        user_id=second_persisted_user.id,
        account_name="second_account",
        account_type="savings",
        institution="second_account_institution",
        masked_number="0002",
    )

    accounts = await account_dao.list_accounts_by_user(persisted_user.id)

    assert len(accounts) == 1
    assert accounts[0].id == first_account.id
    assert accounts[0].user_id == persisted_user.id
    assert not any(account.id == second_account.id for account in accounts)
    assert not any(account.user_id == second_persisted_user.id for account in accounts)


async def test_update_mapping(created_account, db_session, persisted_user):
    account_dao = AccountDao(db_session)
    test_mapping = get_update_account_payload()["mapping"]

    updated = await account_dao.update_mapping(
        user_id=persisted_user.id, account_id=created_account.id, mapping=test_mapping
    )
    await db_session.refresh(created_account)

    assert updated is True
    assert created_account.mapping == test_mapping


async def test_update_mapping_with_wrong_user(
    created_account, db_session, second_persisted_user
):
    account_dao = AccountDao(db_session)
    test_mapping = get_update_account_payload()["mapping"]

    updated = await account_dao.update_mapping(
        user_id=second_persisted_user.id,
        account_id=created_account.id,
        mapping=test_mapping,
    )
    await db_session.refresh(created_account)

    assert updated is False
    assert created_account.mapping is None


async def test_update_mapping_replaces_old(created_account, db_session, persisted_user):
    account_dao = AccountDao(db_session)
    test_mapping = get_update_account_payload()["mapping"]

    await account_dao.update_mapping(
        user_id=persisted_user.id, account_id=created_account.id, mapping=test_mapping
    )
    await db_session.refresh(created_account)

    second_mapping = {
        "posted_at": "second_posted_at",
        "amount": "second_amount",
        "description": "second_description",
        "running_balance": "second_running_balance",
        "raw_type": "second_raw_type",
        "date_format": "second_date_format",
    }

    updated = await account_dao.update_mapping(
        user_id=persisted_user.id, account_id=created_account.id, mapping=second_mapping
    )
    await db_session.refresh(created_account)

    assert updated is True
    assert created_account.mapping == second_mapping


async def test_update_mapping_with_same_mapping_twice(
    created_account, db_session, persisted_user
):
    account_dao = AccountDao(db_session)
    test_mapping = get_update_account_payload()["mapping"]

    # Update mapping twice
    await account_dao.update_mapping(
        user_id=persisted_user.id, account_id=created_account.id, mapping=test_mapping
    )
    updated = await account_dao.update_mapping(
        user_id=persisted_user.id, account_id=created_account.id, mapping=test_mapping
    )
    await db_session.refresh(created_account)

    assert updated is True


async def test_deleting_user_deletes_their_accounts(
    db_session, persisted_user, created_account
):
    await db_session.delete(persisted_user)
    await db_session.flush()

    account_dao = AccountDao(db_session)
    accounts = await account_dao.list_accounts_by_user(persisted_user.id)

    assert len(accounts) == 0
