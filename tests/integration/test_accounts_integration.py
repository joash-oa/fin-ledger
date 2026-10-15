import uuid

import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.core.db import get_db_session
from app.main import app
from tests.factories import (
    get_create_account_payload,
    get_register_payload,
    get_update_account_payload,
    get_users_payloads,
)


@pytest_asyncio.fixture
async def first_user_client(test_db_session):
    app.dependency_overrides[get_db_session] = test_db_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test"
    ) as async_client:
        yield async_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def second_user_client(test_db_session):
    app.dependency_overrides[get_db_session] = test_db_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test"
    ) as async_client:
        yield async_client
    app.dependency_overrides.clear()


def assert_response_matches_payload(response, payload):
    for response_item, payload_item in zip(response, payload):
        assert response_item["account_name"] == payload_item["account_name"]
        assert response_item["account_type"] == payload_item["account_type"]
        assert response_item["masked_number"] == payload_item["masked_number"]
        assert response_item["institution"] == payload_item["institution"]


async def test_accounts_full_cycle(client):
    register_payload = get_register_payload()
    res = await client.post("/auth/register", json=register_payload)

    assert res.status_code == status.HTTP_201_CREATED

    res = await client.get("/accounts")
    body = res.json()

    assert res.status_code == status.HTTP_200_OK
    assert len(body["accounts"]) == 0
    assert body["net_balance"] is None

    create_account_payload = get_create_account_payload()
    res = await client.post("/accounts", json=create_account_payload)

    assert res.status_code == status.HTTP_201_CREATED

    account_id = res.json()["account_id"]

    res = await client.get("/accounts")
    body = res.json()

    assert res.status_code == status.HTTP_200_OK
    assert len(body["accounts"]) == 1
    assert body["accounts"][0]["account_id"] == account_id

    res = await client.get(f"/accounts/{account_id}")
    body = res.json()

    assert res.status_code == status.HTTP_200_OK
    assert body["account_id"] == account_id
    assert_response_matches_payload([body], [create_account_payload])
    assert body["balance"] is None
    assert body["mapping"] is None

    update_account_mapping_payload = get_update_account_payload()
    res = await client.patch(
        f"/accounts/{account_id}", json=update_account_mapping_payload
    )

    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert not res.content

    res = await client.get(f"/accounts/{account_id}")
    body = res.json()

    assert res.status_code == status.HTTP_200_OK
    assert body["account_id"] == account_id
    assert body["mapping"] == update_account_mapping_payload["mapping"]


async def test_create_duplicate_account(client):
    register_payload = get_register_payload()
    res = await client.post("/auth/register", json=register_payload)

    assert res.status_code == status.HTTP_201_CREATED

    create_account_payload = get_create_account_payload()
    res = await client.post("/accounts", json=create_account_payload)

    assert res.status_code == status.HTTP_201_CREATED

    # try to create again, should return 409
    res = await client.post("/accounts", json=create_account_payload)
    assert res.status_code == status.HTTP_409_CONFLICT

    res = await client.get("/accounts")
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()["accounts"]) == 1


async def test_accounts_list_scoped_to_user(first_user_client, second_user_client):
    first_user_payload, second_user_payload = get_users_payloads()
    first_res = await first_user_client.post("/auth/register", json=first_user_payload)
    second_res = await second_user_client.post(
        "/auth/register", json=second_user_payload
    )
    assert first_res.status_code == second_res.status_code == status.HTTP_201_CREATED

    first_user_accounts_payloads = [
        {
            "account_name": "first_account_name",
            "account_type": "checking",
            "masked_number": "0011",
            "institution": "first_account_institution",
        },
        {
            "account_name": "first_account_name_2",
            "account_type": "savings",
            "masked_number": "0012",
            "institution": "first_account_institution",
        },
    ]

    second_user_accounts_payloads = [
        {
            "account_name": "second_account_name",
            "account_type": "checking",
            "masked_number": "0021",
            "institution": "second_account_institution",
        },
        {
            "account_name": "second_account_name_2",
            "account_type": "savings",
            "masked_number": "0022",
            "institution": "second_account_institution",
        },
    ]

    for first_user_account_payload, second_user_account_payload in zip(
        first_user_accounts_payloads, second_user_accounts_payloads
    ):
        first_res = await first_user_client.post(
            "/accounts", json=first_user_account_payload
        )
        second_res = await second_user_client.post(
            "/accounts", json=second_user_account_payload
        )

        assert (
            first_res.status_code == second_res.status_code == status.HTTP_201_CREATED
        )

    first_res = await first_user_client.get("/accounts")
    second_res = await second_user_client.get("/accounts")

    assert first_res.status_code == second_res.status_code == status.HTTP_200_OK

    first_user_accounts = first_res.json()["accounts"]
    second_user_accounts = second_res.json()["accounts"]

    assert len(first_user_accounts) == len(second_user_accounts) == 2

    # Test user accounts are returned created_at order, tiebreaker by id
    assert_response_matches_payload(first_user_accounts, first_user_accounts_payloads)
    assert_response_matches_payload(second_user_accounts, second_user_accounts_payloads)


async def test_get_and_update_with_wrong_user(first_user_client, second_user_client):
    first_user_payload, second_user_payload = get_users_payloads()
    first_res = await first_user_client.post("/auth/register", json=first_user_payload)
    second_res = await second_user_client.post(
        "/auth/register", json=second_user_payload
    )
    assert first_res.status_code == second_res.status_code == status.HTTP_201_CREATED

    non_existing_id = uuid.uuid4()
    non_existing_account_res = await first_user_client.get(
        f"/accounts/{non_existing_id}"
    )
    non_existing_body = non_existing_account_res.json()

    create_first_user_account_payload = {
        "account_name": "first_account_name",
        "account_type": "checking",
        "masked_number": "0001",
        "institution": "first_account_institution",
    }

    first_res = await first_user_client.post(
        "/accounts", json=create_first_user_account_payload
    )
    assert first_res.status_code == status.HTTP_201_CREATED

    first_user_account_id = first_res.json()["account_id"]

    # test get first user's account with second user client
    second_res = await second_user_client.get(f"/accounts/{first_user_account_id}")
    assert (
        second_res.status_code
        == non_existing_account_res.status_code
        == status.HTTP_404_NOT_FOUND
    )
    assert second_res.json() == non_existing_body

    # test patch first user's account with second user client
    upload_account_payload = get_update_account_payload()
    second_res = await second_user_client.patch(
        f"/accounts/{first_user_account_id}", json=upload_account_payload
    )
    assert (
        second_res.status_code
        == non_existing_account_res.status_code
        == status.HTTP_404_NOT_FOUND
    )
    assert second_res.json() == non_existing_body

    # test patch did not change first user's account mapping
    first_res = await first_user_client.get(f"/accounts/{first_user_account_id}")
    assert first_res.status_code == status.HTTP_200_OK

    body = first_res.json()
    assert body["mapping"] is None
