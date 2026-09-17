import io
import pytest


async def get_auth_token(async_client, email: str = "docuser@example.com"):
    reg_payload = {"email": email, "password": "Password123!", "full_name": "Doc User"}
    await async_client.post("/api/v1/auth/register", json=reg_payload)
    login_res = await async_client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return login_res.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_document_upload_and_management_flow(async_client):
    token_a = await get_auth_token(async_client, "usera@example.com")
    token_b = await get_auth_token(async_client, "userb@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Upload valid TXT document as User A
    file_content = b"This is a sample document for testing RAG chunking and vector storage."
    files = {"file": ("sample_policy.txt", io.BytesIO(file_content), "text/plain")}
    upload_res = await async_client.post("/api/v1/documents/upload", headers=headers_a, files=files)
    assert upload_res.status_code == 201
    doc_data = upload_res.json()["data"]
    doc_id = doc_data["id"]
    assert doc_data["filename"] == "sample_policy.txt"
    assert doc_data["status"] == "UPLOADED"

    # 2. Upload unsupported file type (.exe) should fail
    bad_files = {"file": ("malware.exe", io.BytesIO(b"binary content"), "application/octet-stream")}
    bad_upload = await async_client.post("/api/v1/documents/upload", headers=headers_a, files=bad_files)
    assert bad_upload.status_code == 400
    assert bad_upload.json()["error"]["code"] == "INVALID_FILE"

    # 3. List documents as User A
    list_res = await async_client.get("/api/v1/documents", headers=headers_a)
    assert list_res.status_code == 200
    assert list_res.json()["data"]["total"] == 1

    # 4. User B cannot see User A's document in list
    list_b_res = await async_client.get("/api/v1/documents", headers=headers_b)
    assert list_b_res.status_code == 200
    assert list_b_res.json()["data"]["total"] == 0

    # 5. User B cannot fetch User A's document details (404 / Tenant Isolation)
    detail_b_res = await async_client.get(f"/api/v1/documents/{doc_id}", headers=headers_b)
    assert detail_b_res.status_code == 404

    # 6. User A can fetch document details
    detail_a_res = await async_client.get(f"/api/v1/documents/{doc_id}", headers=headers_a)
    assert detail_a_res.status_code == 200
    assert detail_a_res.json()["data"]["id"] == doc_id

    # 7. User A deletes document
    del_res = await async_client.delete(f"/api/v1/documents/{doc_id}", headers=headers_a)
    assert del_res.status_code == 200

    # 8. Document list is now empty for User A
    empty_list = await async_client.get("/api/v1/documents", headers=headers_a)
    assert empty_list.json()["data"]["total"] == 0
