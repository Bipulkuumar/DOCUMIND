import io
import pytest
from tests.integration.test_documents import get_auth_token


@pytest.mark.asyncio
async def test_grounded_rag_chat_and_citations(async_client):
    token = await get_auth_token(async_client, "rag_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload sample policy document
    doc_text = (
        b"# Corporate Security Policy\n"
        b"All employees must complete mandatory cybersecurity training annually.\n"
        b"Passphrases must be a minimum of 16 characters long.\n"
        b"Remote access requires multi-factor authentication (MFA)."
    )
    files = {"file": ("security_policy.md", io.BytesIO(doc_text), "text/markdown")}
    upload_res = await async_client.post("/api/v1/documents/upload", headers=headers, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["data"]["id"]

    # 2. Ask question present in document
    chat_payload = {
        "message": "What is the policy on password length and multi-factor authentication?",
        "top_k": 3
    }
    chat_res = await async_client.post("/api/v1/chat", headers=headers, json=chat_payload)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()["data"]
    assert "conversation_id" in chat_data
    assert "message_id" in chat_data
    assert chat_data["answer"] != ""
    assert len(chat_data["citations"]) >= 1

    citation = chat_data["citations"][0]
    assert citation["document_id"] == doc_id
    assert citation["document_name"] == "security_policy.md"
    assert "similarity" in citation

    # 3. Ask question NOT present in document -> triggers fallback
    unrelated_payload = {
        "message": "What is the company budget for astronaut space suits in 2030?",
        "similarity_threshold": 0.85
    }
    fallback_res = await async_client.post("/api/v1/chat", headers=headers, json=unrelated_payload)
    assert fallback_res.status_code == 200
    fallback_data = fallback_res.json()["data"]
    assert "couldn't find" in fallback_data["answer"].lower() or "not found" in fallback_data["answer"].lower()
    assert len(fallback_data["citations"]) == 0
