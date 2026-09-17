import io
import pytest
from tests.integration.test_documents import get_auth_token


@pytest.mark.asyncio
async def test_semantic_search_flow(async_client):
    token_a = await get_auth_token(async_client, "search_usera@example.com")
    token_b = await get_auth_token(async_client, "search_userb@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Upload sample document as User A
    doc_content = (
        b"# Corporate Refund Policy\n"
        b"Our company provides a full refund within 30 days of purchase for all software products.\n"
        b"To initiate a refund, please contact customer support at support@documind.ai.\n\n"
        b"## Executive Leave Policy\n"
        b"Employees receive 20 days of paid annual leave per calendar year."
    )
    files = {"file": ("refund_policy.md", io.BytesIO(doc_content), "text/markdown")}
    upload_res = await async_client.post("/api/v1/documents/upload", headers=headers_a, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["data"]["id"]

    # 2. Perform semantic search as User A
    search_payload = {
        "query": "What is the policy on refunds and returns?",
        "top_k": 3
    }
    search_res = await async_client.post("/api/v1/search", headers=headers_a, json=search_payload)
    assert search_res.status_code == 200
    search_data = search_res.json()["data"]
    assert search_data["total_results"] >= 1
    top_result = search_data["results"][0]
    assert top_result["document_id"] == doc_id
    assert top_result["document_name"] == "refund_policy.md"
    assert "refund" in top_result["content"].lower()

    # 3. User B performs search -> 0 results (Tenant Isolation)
    search_b_res = await async_client.post("/api/v1/search", headers=headers_b, json=search_payload)
    assert search_b_res.status_code == 200
    assert search_b_res.json()["data"]["total_results"] == 0

    # 4. Search with document_ids filter
    filter_payload = {
        "query": "paid annual leave",
        "top_k": 5,
        "document_ids": [doc_id]
    }
    filter_res = await async_client.post("/api/v1/search", headers=headers_a, json=filter_payload)
    assert filter_res.status_code == 200
    assert filter_res.json()["data"]["total_results"] >= 1
    assert filter_res.json()["data"]["results"][0]["document_id"] == doc_id
