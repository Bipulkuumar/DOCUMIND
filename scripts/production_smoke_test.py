#!/usr/bin/env python3
"""
DocuMind Production Smoke Test Script

This script verifies a deployed or running DocuMind API instance end-to-end:
1. Health endpoint status check
2. User registration and authentication (JWT issue)
3. Document upload & extraction status polling
4. Semantic search execution
5. Grounded RAG chat execution with source citation validation
6. Cross-tenant isolation verification (negative access check)
7. Resource cleanup (document deletion)

Usage:
    python scripts/production_smoke_test.py --url http://localhost:8000
"""

import argparse
import sys
import time
import uuid
import requests


def run_smoke_test(base_url: str):
    print("=" * 60)
    print(f"  DocuMind Production Smoke Test: {base_url}")
    print("=" * 60)

    api_v1 = f"{base_url.rstrip('/')}/api/v1"
    session_id = uuid.uuid4().hex[:8]
    user_a_email = f"smoketest_a_{session_id}@example.com"
    user_b_email = f"smoketest_b_{session_id}@example.com"
    password = "SmokeTestPassword123!"

    # 1. Health Check
    print("\n[1/7] Testing Health Endpoints...")
    try:
        r = requests.get(f"{base_url.rstrip('/')}/health", timeout=10)
        assert r.status_code == 200, f"Root /health status {r.status_code}"
        health_data = r.json()
        print(f"  ✓ Root /health OK: status={health_data.get('status')}")
    except Exception as e:
        print(f"  ✗ Health Check Failed: {e}")
        sys.exit(1)

    # 2. Authentication - User A
    print("\n[2/7] Registering & Authenticating User A...")
    r_reg = requests.post(
        f"{api_v1}/auth/register",
        json={"email": user_a_email, "password": password, "full_name": "Smoke User A"},
        timeout=10,
    )
    assert r_reg.status_code == 201, f"Registration failed: {r_reg.text}"
    token_a = r_reg.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    print(f"  ✓ User A registered and obtained JWT successfully.")

    # Register User B for tenant isolation test
    r_reg_b = requests.post(
        f"{api_v1}/auth/register",
        json={"email": user_b_email, "password": password, "full_name": "Smoke User B"},
        timeout=10,
    )
    assert r_reg_b.status_code == 201, f"User B registration failed: {r_reg_b.text}"
    token_b = r_reg_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    print(f"  ✓ User B registered for isolation checks.")

    # 3. Document Upload
    print("\n[3/7] Uploading Test Document for User A...")
    sample_content = (
        "DocuMind Policy Guidelines 2026.\n"
        "Security Requirement 1: All API requests must use TLS 1.3 encryption.\n"
        "Security Requirement 2: Database passwords must be managed using vault secrets.\n"
        "Contact security@documind.internal for emergency incidents."
    )
    files = {"file": ("smoke_test_policy.txt", sample_content.encode("utf-8"), "text/plain")}
    r_up = requests.post(f"{api_v1}/documents/upload", headers=headers_a, files=files, timeout=15)
    assert r_up.status_code == 202, f"Upload failed: {r_up.text}"
    doc_id = r_up.json()["data"]["id"]
    print(f"  ✓ Document uploaded successfully. ID: {doc_id}")

    # Poll processing status
    print("  Polling document status...")
    max_retries = 15
    for i in range(max_retries):
        r_status = requests.get(f"{api_v1}/documents/{doc_id}", headers=headers_a, timeout=10)
        status_val = r_status.json()["data"]["status"]
        if status_val == "ready":
            print(f"  ✓ Document status: READY after {(i+1)*2}s")
            break
        elif status_val == "failed":
            raise Exception("Document processing status reported FAILED")
        time.sleep(2)
    else:
        raise TimeoutError("Document processing timed out.")

    # 4. Tenant Isolation Check
    print("\n[4/7] Verifying Tenant Isolation (User B accessing User A resource)...")
    r_iso = requests.get(f"{api_v1}/documents/{doc_id}", headers=headers_b, timeout=10)
    assert r_iso.status_code in (403, 404), f"Security breach! User B got status {r_iso.status_code}"
    print(f"  ✓ Tenant Isolation Verified: User B access denied ({r_iso.status_code}).")

    # 5. Semantic Search
    print("\n[5/7] Running Semantic Search...")
    r_search = requests.post(
        f"{api_v1}/search",
        headers=headers_a,
        json={"query": "What version of TLS encryption is required?", "top_k": 3},
        timeout=10,
    )
    assert r_search.status_code == 200, f"Search failed: {r_search.text}"
    results = r_search.json()["data"]["results"]
    assert len(results) > 0, "Semantic search returned empty results"
    print(f"  ✓ Semantic search returned {len(results)} chunks. Top score: {results[0]['score']:.4f}")

    # 6. Grounded RAG Chat & Citation Check
    print("\n[6/7] Running RAG Chat Query...")
    r_chat = requests.post(
        f"{api_v1}/chat",
        headers=headers_a,
        json={"message": "What is the security requirement for API requests?"},
        timeout=20,
    )
    assert r_chat.status_code == 200, f"Chat failed: {r_chat.text}"
    chat_resp = r_chat.json()["data"]
    answer = chat_resp["answer"]
    citations = chat_resp["citations"]
    print(f"  ✓ Answer: {answer[:120]}...")
    print(f"  ✓ Citations returned: {len(citations)}")
    assert len(citations) > 0, "No citations generated for grounded answer!"

    # 7. Cleanup
    print("\n[7/7] Cleaning Up Test Artifacts...")
    r_del = requests.delete(f"{api_v1}/documents/{doc_id}", headers=headers_a, timeout=10)
    assert r_del.status_code == 200, f"Document deletion failed: {r_del.text}"
    print("  ✓ Test document deleted successfully.")

    print("\n" + "=" * 60)
    print("  PRODUCTION SMOKE TEST PASSED SUCCESSFULLY 🎉")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DocuMind Production Smoke Test")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of DocuMind API")
    args = parser.parse_args()
    try:
        run_smoke_test(args.url)
    except Exception as err:
        print(f"\n❌ SMOKE TEST FAILED: {err}")
        sys.exit(1)
