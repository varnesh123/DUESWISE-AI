"""Integration tests for ingestion API endpoints — CONTRACT.md §6."""

import io
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def auth_headers(client):
    client.post("/api/v1/auth/demo", json={"persona": "salaried"})
    return {"Authorization": "Bearer 11111111-1111-4111-8111-111111111111"}


# ---------- SMS ingestion ----------

def test_ingest_sms_upi(client, auth_headers):
    response = client.post(
        "/api/v1/transactions/ingest/sms",
        json={
            "message": "Rs.499 debited from A/c XX1234 for UPI payment to NETFLIX INDIA on 18-11-2026. UPI Ref 123456789012.",
            "source": "sms",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["duplicate"] is False
    assert body["transaction"] is not None
    assert body["transaction"]["amount_paise"] == 49900
    assert body["transaction"]["merchant_normalized"] == "Netflix"
    assert body["transaction"]["category"] == "entertainment"
    assert body["transaction"]["source"] == "sms"


def test_ingest_sms_duplicate(client, auth_headers):
    msg = "Rs.499 debited from A/c XX1234 for UPI payment to NETFLIX INDIA on 18-11-2026. UPI Ref 123456789012."
    client.post("/api/v1/transactions/ingest/sms", json={"message": msg, "source": "sms"}, headers=auth_headers)
    response = client.post("/api/v1/transactions/ingest/sms", json={"message": msg, "source": "sms"}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["duplicate"] is True


def test_ingest_sms_unparseable(client, auth_headers):
    response = client.post(
        "/api/v1/transactions/ingest/sms",
        json={"message": "Hello, this is not a transaction.", "source": "sms"},
        headers=auth_headers,
    )
    assert response.status_code == 422
    body = response.json()
    assert "error" in body


# ---------- File ingestion (CSV) ----------

def test_ingest_csv_file(client, auth_headers):
    csv_content = (
        b"date,merchant,amount,type,payment_method,reference\n"
        b"2026-11-18,NETFLIX INDIA,499.00,debit,upi,REF123\n"
        b"2026-11-19,AMAZON IN,1200.00,debit,card,REF456\n"
    )
    response = client.post(
        "/api/v1/transactions/ingest/file",
        files={"file": ("statement.csv", io.BytesIO(csv_content), "text/csv")},
        data={"source": "csv"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["imported_count"] == 2
    assert body["rejected_count"] == 0


def test_ingest_unsupported_file_type(client, auth_headers):
    response = client.post(
        "/api/v1/transactions/ingest/file",
        files={"file": ("statement.xls", io.BytesIO(b"data"), "application/vnd.ms-excel")},
        data={"source": "csv"},
        headers=auth_headers,
    )
    assert response.status_code == 415


def test_ingest_invalid_source(client, auth_headers):
    response = client.post(
        "/api/v1/transactions/ingest/file",
        files={"file": ("statement.csv", io.BytesIO(b"data"), "text/csv")},
        data={"source": "invalid"},
        headers=auth_headers,
    )
    assert response.status_code == 415


# ---------- AA mock ingestion ----------

def test_ingest_aa_mock(client, auth_headers):
    response = client.post(
        "/api/v1/transactions/ingest/aa-mock",
        json={
            "consent_id": "mock-consent-001",
            "account_reference": "mock-account-001",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["source"] == "aa_mock"
    assert body["imported_count"] == 3


def test_ingest_aa_mock_duplicate(client, auth_headers):
    payload = {
        "consent_id": "mock-consent-001",
        "account_reference": "mock-account-001",
    }
    client.post("/api/v1/transactions/ingest/aa-mock", json=payload, headers=auth_headers)
    response = client.post("/api/v1/transactions/ingest/aa-mock", json=payload, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["duplicates_skipped"] == 3
    assert body["imported_count"] == 0


# ---------- User isolation ----------

def test_user_isolation_ingestion(client):
    # User A creates a transaction via SMS
    client.post("/api/v1/auth/demo", json={"persona": "salaried"})
    headers_a = {"Authorization": "Bearer 11111111-1111-4111-8111-111111111111"}
    client.post(
        "/api/v1/transactions/ingest/sms",
        json={"message": "Rs.499 debited from A/c XX1234 for UPI payment to NETFLIX INDIA on 18-11-2026. UPI Ref 123456789012.", "source": "sms"},
        headers=headers_a,
    )

    # User B should not see it
    client.post("/api/v1/auth/demo", json={"persona": "shopkeeper"})
    headers_b = {"Authorization": "Bearer 33333333-3333-4333-8333-333333333333"}
    response = client.get("/api/v1/transactions", headers=headers_b)
    assert response.status_code == 200
    assert response.json()["total"] == 0
