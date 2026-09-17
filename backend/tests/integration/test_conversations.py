import pytest
from tests.integration.test_documents import get_auth_token


@pytest.mark.asyncio
async def test_conversation_management_and_isolation(async_client):
    token_a = await get_auth_token(async_client, "conv_usera@example.com")
    token_b = await get_auth_token(async_client, "conv_userb@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Send chat message as User A to start a conversation
    chat_payload = {"message": "Hello, how does DocuMind work?"}
    chat_res = await async_client.post("/api/v1/chat", headers=headers_a, json=chat_payload)
    assert chat_res.status_code == 200
    conv_id = chat_res.json()["data"]["conversation_id"]

    # 2. List conversations as User A
    list_a = await async_client.get("/api/v1/conversations", headers=headers_a)
    assert list_a.status_code == 200
    assert list_a.json()["data"]["total"] == 1
    assert list_a.json()["data"]["items"][0]["id"] == conv_id

    # 3. List conversations as User B -> 0
    list_b = await async_client.get("/api/v1/conversations", headers=headers_b)
    assert list_b.status_code == 200
    assert list_b.json()["data"]["total"] == 0

    # 4. Fetch detail history as User A
    detail_a = await async_client.get(f"/api/v1/conversations/{conv_id}", headers=headers_a)
    assert detail_a.status_code == 200
    detail_data = detail_a.json()["data"]
    assert len(detail_data["messages"]) == 2  # 1 user, 1 assistant
    assert detail_data["messages"][0]["role"] == "user"
    assert detail_data["messages"][1]["role"] == "assistant"

    # 5. User B cannot access User A's conversation detail
    detail_b = await async_client.get(f"/api/v1/conversations/{conv_id}", headers=headers_b)
    assert detail_b.status_code == 404

    # 6. REGRESSION TEST: User B attempts to send chat message using User A's conversation_id -> 404
    unauthorized_chat_res = await async_client.post(
        "/api/v1/chat",
        headers=headers_b,
        json={"conversation_id": conv_id, "message": "Can I read User A's chat?"}
    )
    assert unauthorized_chat_res.status_code == 404
    assert unauthorized_chat_res.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"

    # 7. Delete conversation as User A
    del_res = await async_client.delete(f"/api/v1/conversations/{conv_id}", headers=headers_a)
    assert del_res.status_code == 200

    # 8. List is now empty
    empty_list = await async_client.get("/api/v1/conversations", headers=headers_a)
    assert empty_list.json()["data"]["total"] == 0
