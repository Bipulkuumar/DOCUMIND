import pytest


@pytest.mark.asyncio
async def test_user_registration_and_login_flow(async_client):
    # 1. Register a new user
    register_payload = {
        "email": "testuser@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test User"
    }
    response = await async_client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["email"] == "testuser@example.com"
    assert "id" in res_data["data"]

    # 2. Duplicate registration attempt should fail
    duplicate_res = await async_client.post("/api/v1/auth/register", json=register_payload)
    assert duplicate_res.status_code == 400
    assert duplicate_res.json()["error"]["code"] == "USER_ALREADY_EXISTS"

    # 3. Login with correct credentials
    login_payload = {
        "email": "testuser@example.com",
        "password": "SecurePassword123!"
    }
    login_res = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data["data"]
    token = login_data["data"]["access_token"]

    # 4. Login with wrong password should fail
    bad_login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "testuser@example.com",
        "password": "WrongPassword!"
    })
    assert bad_login_res.status_code == 401
    assert bad_login_res.json()["error"]["code"] == "UNAUTHORIZED"

    # 5. Access /auth/me with valid Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()["data"]
    assert me_data["email"] == "testuser@example.com"
    assert me_data["full_name"] == "Test User"

    # 6. Access /auth/me without token should fail
    unauth_res = await async_client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401
