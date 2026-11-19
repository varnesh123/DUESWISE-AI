"""Integration tests for contract-aligned endpoints.

Covers the routes the Flutter client depends on:
- POST /api/v1/auth/demo exposing user_id / expires_in_minutes
- GET  /api/v1/dues/{due_id}
- POST /api/v1/transactions/ingest (manual and SMS shapes)
- GET  /api/v1/nudges exposing the contract ``read`` field
- Standard error codes for method-not-allowed responses
"""

import pytest


@pytest.fixture
def auth_headers(client):
    client.post("/api/v1/auth/demo", json={"persona": "salaried"})
    return {"Authorization": "Bearer 11111111-1111-4111-8111-111111111111"}


# ---------- Auth response shape ----------

def test_demo_response_includes_flutter_fields(client):
    response = client.post("/api/v1/auth/demo", json={"persona": "salaried"})
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "11111111-1111-4111-8111-111111111111"
    assert body["access_token"] == body["user_id"]
    assert body["expires_in_minutes"] == 30
    assert body["token_type"] == "bearer"
    assert body["user"]["id"] == body["user_id"]


# ---------- Due detail ----------

def test_get_due_by_id(client, auth_headers):
    created = client.post(
        "/api/v1/dues",
        json={
            "title": "Home EMI",
            "due_type": "emi",
            "amount_paise": 2000000,
            "due_date": "2026-11-25",
            "frequency": "monthly",
            "is_mandatory": True,
        },
        headers=auth_headers,
    )
    due_id = created.json()["id"]

    response = client.get(f"/api/v1/dues/{due_id}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == due_id
    assert body["title"] == "Home EMI"
    assert body["amount_paise"] == 2000000


def test_get_due_not_found(client, auth_headers):
    response = client.get(
        "/api/v1/dues/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_get_due_is_user_scoped(client):
    client.post("/api/v1/auth/demo", json={"persona": "salaried"})
    headers_a = {"Authorization": "Bearer 11111111-1111-4111-8111-111111111111"}
    created = client.post(
        "/api/v1/dues",
        json={
            "title": "Private due",
            "due_type": "rent",
            "amount_paise": 100000,
            "due_date": "2026-12-01",
            "frequency": "monthly",
            "is_mandatory": True,
        },
        headers=headers_a,
    )
    due_id = created.json()["id"]

    client.post("/api/v1/auth/demo", json={"persona": "shopkeeper"})
    headers_b = {"Authorization": "Bearer 33333333-3333-4333-8333-333333333333"}
    response = client.get(f"/api/v1/dues/{due_id}", headers=headers_b)
    assert response.status_code == 404


# ---------- Unified ingestion ----------

def test_ingest_manual_transaction(client, auth_headers):
    response = client.post(
        "/api/v1/transactions/ingest",
        json={
            "merchant_raw": "NETFLIX INDIA",
            "amount_paise": 89900,
            "transaction_type": "debit",
            "category": "entertainment",
            "transaction_date": "2026-11-18",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["duplicate"] is False
    assert body["transaction"]["amount_paise"] == 89900
    assert body["transaction"]["merchant_normalized"] == "Netflix"
    assert body["transaction"]["category"] == "entertainment"
    assert body["transaction"]["source"] == "manual"
    assert body["transaction"]["transaction_date"] == "2026-11-18"


def test_ingest_manual_defaults_date_to_today(client, auth_headers):
    response = client.post(
        "/api/v1/transactions/ingest",
        json={"merchant": "LOCAL KIRANA", "amount_paise": 25500},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["transaction"]["transaction_date"]


def test_ingest_manual_duplicate(client, auth_headers):
    payload = {
        "merchant_raw": "NETFLIX INDIA",
        "amount_paise": 89900,
        "transaction_type": "debit",
        "transaction_date": "2026-11-18",
    }
    first = client.post("/api/v1/transactions/ingest", json=payload, headers=auth_headers)
    assert first.status_code == 200
    second = client.post("/api/v1/transactions/ingest", json=payload, headers=auth_headers)
    assert second.status_code == 200
    body = second.json()
    assert body["duplicate"] is True
    assert body["transaction"]["amount_paise"] == 89900


def test_ingest_sms_shape(client, auth_headers):
    response = client.post(
        "/api/v1/transactions/ingest",
        json={
            "message": "Rs.499 debited from A/c XX1234 for UPI payment to NETFLIX INDIA on 18-11-2026. UPI Ref 987654321012.",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["transaction"]["merchant_normalized"] == "Netflix"
    assert body["processing"]["source"] == "sms"


def test_ingest_requires_a_merchant_or_message(client, auth_headers):
    response = client.post(
        "/api/v1/transactions/ingest",
        json={"amount_paise": 1000},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_ingest_rejects_bad_date(client, auth_headers):
    response = client.post(
        "/api/v1/transactions/ingest",
        json={
            "merchant_raw": "TEST",
            "amount_paise": 1000,
            "transaction_date": "18-11-2026",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_ingest_requires_auth(client):
    response = client.post(
        "/api/v1/transactions/ingest",
        json={"merchant_raw": "TEST", "amount_paise": 1000},
    )
    assert response.status_code == 401


# ---------- Nudge contract field ----------

def test_nudges_expose_read_flag(client, auth_headers):
    response = client.get("/api/v1/nudges", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    for item in body["items"]:
        assert "read" in item
        assert item["read"] == (item["status"] == "read")


# ---------- Error classification ----------

def test_method_not_allowed_uses_contract_code(client):
    response = client.post("/health")
    assert response.status_code == 405
    body = response.json()
    assert body["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert "error" in body
