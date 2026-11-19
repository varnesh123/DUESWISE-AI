"""Integration tests for transaction API endpoints — CONTRACT.md §5."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def auth_headers(client):
    """Create a demo session and return auth headers."""
    client.post("/api/v1/auth/demo", json={"persona": "salaried"})
    return {"Authorization": "Bearer 11111111-1111-4111-8111-111111111111"}


def test_create_manual_transaction(client, auth_headers):
    response = client.post(
        "/api/v1/transactions/manual",
        json={
            "amount_paise": 25000,
            "transaction_type": "debit",
            "merchant": "Local grocery store",
            "category": "groceries",
            "payment_method": "upi",
            "transaction_date": "2026-11-19",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["amount_paise"] == 25000
    assert body["transaction_type"] == "debit"
    assert body["merchant_raw"] == "Local grocery store"
    assert body["merchant_normalized"] == "Local grocery store"
    assert body["category"] == "groceries"
    assert body["payment_method"] == "upi"
    assert body["transaction_date"] == "2026-11-19"
    assert body["source"] == "manual"
    assert body["is_suspicious"] is False
    assert "id" in body


def test_create_manual_transaction_duplicate(client, auth_headers):
    payload = {
        "amount_paise": 25000,
        "transaction_type": "debit",
        "merchant": "Local grocery store",
        "category": "groceries",
        "payment_method": "upi",
        "transaction_date": "2026-11-19",
    }
    client.post("/api/v1/transactions/manual", json=payload, headers=auth_headers)
    response = client.post("/api/v1/transactions/manual", json=payload, headers=auth_headers)
    assert response.status_code == 409


def test_create_manual_transaction_invalid_date(client, auth_headers):
    response = client.post(
        "/api/v1/transactions/manual",
        json={
            "amount_paise": 25000,
            "transaction_type": "debit",
            "merchant": "Store",
            "payment_method": "upi",
            "transaction_date": "not-a-date",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_create_manual_transaction_negative_amount(client, auth_headers):
    response = client.post(
        "/api/v1/transactions/manual",
        json={
            "amount_paise": -100,
            "transaction_type": "debit",
            "merchant": "Store",
            "payment_method": "upi",
            "transaction_date": "2026-11-19",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_list_transactions(client, auth_headers):
    # Create a couple of transactions
    client.post(
        "/api/v1/transactions/manual",
        json={
            "amount_paise": 25000,
            "transaction_type": "debit",
            "merchant": "Grocery Store",
            "category": "groceries",
            "payment_method": "upi",
            "transaction_date": "2026-11-19",
        },
        headers=auth_headers,
    )
    client.post(
        "/api/v1/transactions/manual",
        json={
            "amount_paise": 49900,
            "transaction_type": "debit",
            "merchant": "Netflix",
            "category": "entertainment",
            "payment_method": "upi",
            "transaction_date": "2026-11-18",
        },
        headers=auth_headers,
    )

    response = client.get("/api/v1/transactions", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert "page" in body
    assert "page_size" in body
    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_list_transactions_pagination(client, auth_headers):
    for i in range(5):
        client.post(
            "/api/v1/transactions/manual",
            json={
                "amount_paise": 1000 * (i + 1),
                "transaction_type": "debit",
                "merchant": f"Merchant {i}",
                "category": "groceries",
                "payment_method": "upi",
                "transaction_date": f"2026-11-{i + 1:02d}",
            },
            headers=auth_headers,
        )

    response = client.get("/api/v1/transactions?page=1&page_size=3", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 3
    assert body["page"] == 1
    assert body["page_size"] == 3


def test_list_transactions_category_filter(client, auth_headers):
    client.post(
        "/api/v1/transactions/manual",
        json={
            "amount_paise": 25000,
            "transaction_type": "debit",
            "merchant": "Grocery Store",
            "category": "groceries",
            "payment_method": "upi",
            "transaction_date": "2026-11-19",
        },
        headers=auth_headers,
    )
    client.post(
        "/api/v1/transactions/manual",
        json={
            "amount_paise": 49900,
            "transaction_type": "debit",
            "merchant": "Netflix",
            "category": "entertainment",
            "payment_method": "upi",
            "transaction_date": "2026-11-18",
        },
        headers=auth_headers,
    )

    response = client.get("/api/v1/transactions?category=groceries", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["category"] == "groceries"


def test_get_transaction_by_id(client, auth_headers):
    create_resp = client.post(
        "/api/v1/transactions/manual",
        json={
            "amount_paise": 25000,
            "transaction_type": "debit",
            "merchant": "Test Store",
            "category": "groceries",
            "payment_method": "upi",
            "transaction_date": "2026-11-19",
        },
        headers=auth_headers,
    )
    txn_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/transactions/{txn_id}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == txn_id
    assert body["merchant_raw"] == "Test Store"


def test_get_transaction_not_found(client, auth_headers):
    response = client.get(
        "/api/v1/transactions/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"


def test_transactions_require_auth(client):
    response = client.get("/api/v1/transactions")
    assert response.status_code == 401

    response = client.post(
        "/api/v1/transactions/manual",
        json={
            "amount_paise": 1000,
            "transaction_type": "debit",
            "merchant": "Store",
            "payment_method": "upi",
            "transaction_date": "2026-11-19",
        },
    )
    assert response.status_code == 401
