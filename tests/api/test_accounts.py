import pytest
import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_account_service, get_auth_service
from app.core.exceptions import AccountNotFoundException, DuplicateAccountException
from app.main import app
from tests.constants import (
    TEST_ACCOUNT_ID,
    TEST_ACCOUNT_INSTITUTION,
    TEST_ACCOUNT_NAME,
    TEST_ACCOUNT_TYPE,
    TEST_MASKED_NUMBER,
    TEST_USER_ID,
)
from tests.factories import get_create_account_payload, get_update_account_payload


@pytest_asyncio.fixture()
async def unauthenticated_client(auth_service, account_service):
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_account_service] = lambda: account_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test-user"
    ) as unauthenticated_client:
        yield unauthenticated_client

    app.dependency_overrides.clear()


async def test_create_account_success(client, account_service):
    payload = get_create_account_payload()

    res = await client.post("/accounts", json=payload)
    body = res.json()

    account_service.create_account.assert_awaited_once_with(
        user_id=TEST_USER_ID,
        account_name=TEST_ACCOUNT_NAME,
        account_type=TEST_ACCOUNT_TYPE,
        institution=TEST_ACCOUNT_INSTITUTION,
        masked_number=TEST_MASKED_NUMBER,
    )
    assert res.status_code == status.HTTP_201_CREATED
    assert body["account_id"] == str(TEST_ACCOUNT_ID)


async def test_create_account_with_duplicate_account_same_user(client, account_service):
    account_service.create_account.side_effect = DuplicateAccountException
    payload = get_create_account_payload()

    res = await client.post("/accounts", json=payload)

    account_service.create_account.assert_awaited_once_with(
        user_id=TEST_USER_ID,
        account_name=TEST_ACCOUNT_NAME,
        account_type=TEST_ACCOUNT_TYPE,
        institution=TEST_ACCOUNT_INSTITUTION,
        masked_number=TEST_MASKED_NUMBER,
    )
    assert res.status_code == status.HTTP_409_CONFLICT


async def test_create_account_with_normalized_type(client, account_service):
    payload = get_create_account_payload()
    unnormalized_type = "Checking"
    payload["account_type"] = unnormalized_type

    res = await client.post("/accounts", json=payload)
    account_type = account_service.create_account.call_args.kwargs["account_type"]

    assert res.status_code == status.HTTP_201_CREATED
    assert account_type == unnormalized_type.lower()


async def test_create_account_with_invalid_type(client, account_service):
    payload = get_create_account_payload()
    payload["account_type"] = "Credit"

    res = await client.post("/accounts", json=payload)

    account_service.create_account.assert_not_awaited()
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_create_account_with_leading_zeros_masked_number(client, account_service):
    payload = get_create_account_payload()
    masked_number_zeros = "0509"
    payload["masked_number"] = masked_number_zeros

    res = await client.post("/accounts", json=payload)
    masked_number = account_service.create_account.call_args.kwargs["masked_number"]

    assert res.status_code == status.HTTP_201_CREATED
    assert masked_number == masked_number_zeros


async def test_create_account_with_whitespace_only_account_name(
    client, account_service
):
    payload = get_create_account_payload()
    payload["account_name"] = " "

    res = await client.post("/accounts", json=payload)

    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    account_service.create_account.assert_not_awaited()


async def test_create_account_with_whitespace_only_institution(client, account_service):
    payload = get_create_account_payload()
    payload["institution"] = " "

    res = await client.post("/accounts", json=payload)

    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    account_service.create_account.assert_not_awaited()


async def test_create_account_with_whitespace_account_name(client, account_service):
    payload = get_create_account_payload()
    payload["account_name"] = " test_name "

    res = await client.post("/accounts", json=payload)
    account_name = account_service.create_account.call_args.kwargs["account_name"]

    assert res.status_code == status.HTTP_201_CREATED
    assert account_name == "test_name"


async def test_create_account_with_whitespace_institution(client, account_service):
    payload = get_create_account_payload()
    payload["institution"] = " Chase "

    res = await client.post("/accounts", json=payload)
    institution = account_service.create_account.call_args.kwargs["institution"]

    assert res.status_code == status.HTTP_201_CREATED
    assert institution == "Chase"


@pytest.mark.parametrize("invalid_number", ["", "12345", "12a4", "١٢٣٤", " "])
async def test_create_account_with_invalid_masked_number(
    client, account_service, invalid_number
):
    payload = get_create_account_payload()
    payload["masked_number"] = invalid_number

    res = await client.post("/accounts", json=payload)

    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    account_service.create_account.assert_not_awaited()


async def test_list_accounts_success(client, account_service):
    res = await client.get("/accounts")
    body = res.json()

    assert res.status_code == status.HTTP_200_OK
    assert len(body["accounts"]) == 1
    assert body["accounts"][0]["account_id"] == str(TEST_ACCOUNT_ID)
    assert body["net_balance"] is None
    account_service.list_accounts.assert_awaited_once_with(user_id=TEST_USER_ID)


async def test_list_accounts_does_not_contain_mapping(client, account_service):
    res = await client.get("/accounts")
    body = res.json()

    assert res.status_code == status.HTTP_200_OK
    assert "mapping" not in body["accounts"][0]
    account_service.list_accounts.assert_awaited_once_with(user_id=TEST_USER_ID)


async def test_get_account_success(client, account_service):
    res = await client.get(f"/accounts/{TEST_ACCOUNT_ID}")
    body = res.json()

    assert res.status_code == status.HTTP_200_OK
    account_service.get_account_by_id.assert_awaited_once_with(
        user_id=TEST_USER_ID, account_id=TEST_ACCOUNT_ID
    )
    assert body["account_id"] == str(TEST_ACCOUNT_ID)
    assert body["account_name"] == TEST_ACCOUNT_NAME
    assert body["account_type"] == TEST_ACCOUNT_TYPE
    assert body["institution"] == TEST_ACCOUNT_INSTITUTION
    assert body["masked_number"] == TEST_MASKED_NUMBER
    assert body["balance"] is None
    assert body["mapping"] is None


async def test_get_account_non_existent_id(client, account_service):
    account_service.get_account_by_id.side_effect = AccountNotFoundException

    res = await client.get(f"/accounts/{TEST_ACCOUNT_ID}")

    assert res.status_code == status.HTTP_404_NOT_FOUND
    account_service.get_account_by_id.assert_awaited_once_with(
        user_id=TEST_USER_ID, account_id=TEST_ACCOUNT_ID
    )


async def test_get_account_with_wrong_user(client, account_service):
    """Test get account with wrong user ID returns the same response as non-existent account"""
    account_service.get_account_by_id.side_effect = AccountNotFoundException

    res = await client.get(f"/accounts/{TEST_ACCOUNT_ID}")

    assert res.status_code == status.HTTP_404_NOT_FOUND
    account_service.get_account_by_id.assert_awaited_once_with(
        user_id=TEST_USER_ID, account_id=TEST_ACCOUNT_ID
    )


async def test_patch_account_success(client, account_service):
    payload = get_update_account_payload()

    res = await client.patch(f"/accounts/{TEST_ACCOUNT_ID}", json=payload)

    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert not res.content
    account_service.update_account_mapping.assert_awaited_once_with(
        user_id=TEST_USER_ID, account_id=TEST_ACCOUNT_ID, mapping=payload["mapping"]
    )


async def test_patch_account_with_missing_field_mapping(client, account_service):
    payload = get_update_account_payload()
    del payload["mapping"]["posted_at"]

    res = await client.patch(f"/accounts/{TEST_ACCOUNT_ID}", json=payload)

    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    account_service.update_account_mapping.assert_not_awaited()


async def test_patch_account_with_extra_field_mapping(client, account_service):
    payload = get_update_account_payload()
    payload["mapping"]["test_field"] = "test_value"

    res = await client.patch(f"/accounts/{TEST_ACCOUNT_ID}", json=payload)

    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    account_service.update_account_mapping.assert_not_awaited()


async def test_patch_account_with_invalid_row_order(client, account_service):
    payload = get_update_account_payload()
    payload["mapping"]["row_order"] = "FooBar"

    res = await client.patch(f"/accounts/{TEST_ACCOUNT_ID}", json=payload)

    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    account_service.update_account_mapping.assert_not_awaited()


async def test_patch_account_with_unknown_account(client, account_service):
    account_service.update_account_mapping.side_effect = AccountNotFoundException
    payload = get_update_account_payload()

    res = await client.patch(f"/accounts/{TEST_ACCOUNT_ID}", json=payload)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    account_service.update_account_mapping.assert_awaited_once_with(
        user_id=TEST_USER_ID,
        account_id=TEST_ACCOUNT_ID,
        mapping=payload["mapping"],
    )


async def test_patch_account_with_wrong_user(client, account_service):
    """Test patch account with wrong user ID returns the same response as non-existent account"""
    account_service.update_account_mapping.side_effect = AccountNotFoundException
    payload = get_update_account_payload()

    res = await client.patch(f"/accounts/{TEST_ACCOUNT_ID}", json=payload)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    account_service.update_account_mapping.assert_awaited_once_with(
        user_id=TEST_USER_ID,
        account_id=TEST_ACCOUNT_ID,
        mapping=payload["mapping"],
    )


async def test_patch_account_with_null_mapping(client, account_service):
    payload = {"mapping": None}

    res = await client.patch(f"/accounts/{TEST_ACCOUNT_ID}", json=payload)

    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    account_service.update_account_mapping.assert_not_awaited()


async def test_get_account_by_id_with_no_session_token(
    unauthenticated_client, auth_service, account_service
):
    res = await unauthenticated_client.get(f"/accounts/{TEST_ACCOUNT_ID}")

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    auth_service.authenticate.assert_not_awaited()
    account_service.get_account_by_id.assert_not_awaited()
