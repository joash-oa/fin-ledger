import dataclasses

import pytest

from app.core.exceptions import AccountNotFoundException, DuplicateAccountException
from app.services.account_service import AccountInfo, AccountService
from tests.constants import (
    TEST_ACCOUNT_ID,
    TEST_ACCOUNT_INSTITUTION,
    TEST_ACCOUNT_NAME,
    TEST_ACCOUNT_TYPE,
    TEST_MASKED_NUMBER,
    TEST_USER_ID,
)
from tests.factories import (
    get_create_account_data,
    get_mock_account,
    get_update_account_payload,
)

TEST_ACCOUNT_INFO = AccountInfo(
    account_id=TEST_ACCOUNT_ID,
    account_name=TEST_ACCOUNT_NAME,
    institution=TEST_ACCOUNT_INSTITUTION,
    account_type=TEST_ACCOUNT_TYPE,
    masked_number=TEST_MASKED_NUMBER,
    balance=None,
    mapping=None,
)


async def test_create_account_success(account_dao):
    account_service = AccountService(account_dao)
    create_account_data = get_create_account_data()

    account_id = await account_service.create_account(**create_account_data)

    account_dao.create_account.assert_awaited_once_with(
        user_id=TEST_USER_ID,
        account_name=TEST_ACCOUNT_NAME,
        account_type=TEST_ACCOUNT_TYPE,
        institution=TEST_ACCOUNT_INSTITUTION,
        masked_number=TEST_MASKED_NUMBER,
    )
    assert account_id == TEST_ACCOUNT_ID


async def test_create_account_with_duplicate_account(account_dao):
    account_service = AccountService(account_dao)
    account_dao.create_account.side_effect = DuplicateAccountException

    with pytest.raises(DuplicateAccountException):
        await account_service.create_account(**get_create_account_data())

    account_dao.create_account.assert_awaited_once_with(
        user_id=TEST_USER_ID,
        account_name=TEST_ACCOUNT_NAME,
        account_type=TEST_ACCOUNT_TYPE,
        institution=TEST_ACCOUNT_INSTITUTION,
        masked_number=TEST_MASKED_NUMBER,
    )


async def test_get_account_by_id_success(account_dao):
    account_service = AccountService(account_dao)

    account_info = await account_service.get_account_by_id(
        user_id=TEST_USER_ID, account_id=TEST_ACCOUNT_ID
    )

    account_dao.get_account_by_id.assert_awaited_once_with(
        user_id=TEST_USER_ID, account_id=TEST_ACCOUNT_ID
    )
    assert account_info == TEST_ACCOUNT_INFO


async def test_get_account_by_id_returns_mapping(account_dao):
    test_mapping = get_update_account_payload()["mapping"]
    test_account = get_mock_account()
    test_account.mapping = test_mapping
    account_dao.get_account_by_id.return_value = test_account
    test_account_info = dataclasses.replace(TEST_ACCOUNT_INFO, mapping=test_mapping)
    account_service = AccountService(account_dao)

    account_info = await account_service.get_account_by_id(
        user_id=TEST_USER_ID, account_id=TEST_ACCOUNT_ID
    )

    assert account_info == test_account_info


async def test_get_account_by_id_non_existent_account(account_dao):
    """Behaves the same as get_account for wrong user"""
    account_dao.get_account_by_id.return_value = None
    account_service = AccountService(account_dao)

    with pytest.raises(AccountNotFoundException):
        await account_service.get_account_by_id(
            user_id=TEST_USER_ID, account_id=TEST_ACCOUNT_ID
        )

    account_dao.get_account_by_id.assert_awaited_once_with(
        user_id=TEST_USER_ID, account_id=TEST_ACCOUNT_ID
    )


async def test_list_accounts_success(account_dao):
    account_service = AccountService(account_dao)

    user_accounts = await account_service.list_accounts(user_id=TEST_USER_ID)

    account_dao.list_accounts_by_user.assert_awaited_once_with(user_id=TEST_USER_ID)
    assert len(user_accounts.accounts) == 1
    assert user_accounts.accounts[0] == TEST_ACCOUNT_INFO
    assert user_accounts.net_balance is None


async def test_list_accounts_with_no_accounts(account_dao):
    account_dao.list_accounts_by_user.return_value = []
    account_service = AccountService(account_dao)

    user_accounts = await account_service.list_accounts(user_id=TEST_USER_ID)

    assert len(user_accounts.accounts) == 0
    assert user_accounts.net_balance is None
    account_dao.list_accounts_by_user.assert_awaited_once_with(user_id=TEST_USER_ID)


async def test_update_account_mapping_success(account_dao):
    test_mapping = get_update_account_payload()["mapping"]
    account_service = AccountService(account_dao)

    await account_service.update_account_mapping(
        user_id=TEST_USER_ID, account_id=TEST_ACCOUNT_ID, mapping=test_mapping
    )

    account_dao.update_mapping.assert_awaited_once_with(
        user_id=TEST_USER_ID, account_id=TEST_ACCOUNT_ID, mapping=test_mapping
    )


async def test_update_account_mapping_wrong_user(account_dao):
    test_mapping = get_update_account_payload()["mapping"]
    account_service = AccountService(account_dao)
    account_dao.update_mapping.return_value = False

    with pytest.raises(AccountNotFoundException):
        await account_service.update_account_mapping(
            user_id=TEST_USER_ID, account_id=TEST_ACCOUNT_ID, mapping=test_mapping
        )

    account_dao.update_mapping.assert_awaited_once_with(
        user_id=TEST_USER_ID, account_id=TEST_ACCOUNT_ID, mapping=test_mapping
    )
