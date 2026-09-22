from tests.constants import TEST_SESSION_TOKEN, TEST_USER_ID


async def test_register(client, auth_service):
    register_payload = {
        "first_name": "test_first",
        "last_name": "test_last",
        "email": "test@email.com",
        "password": "Password123",
    }
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
