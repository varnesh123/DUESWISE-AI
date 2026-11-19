"""Integration tests for dues API — CONTRACT.md §7."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def auth_headers(client):
    client.post("/api/v1/auth/demo", json={"persona": "salaried"})
    return {"Authorization": "Bearer 11111111-1111-4111-8111-111111111111"}


def test_create_due(client, auth_headers):
    response = client.post(
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
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Home EMI"
    assert body["due_type"] == "emi"
    assert body["amount_paise"] == 2000000
    assert body["due_date"] == "2026-11-25"
    assert body["frequency"] == "monthly"
    assert body["status"] == "upcoming"
    assert body["is_mandatory"] is True
    assert body["source"] == "manual"
    assert "id" in body


def test_list_dues(client, auth_headers):
    client.post(
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
    client.post(
        "/api/v1/dues",
        json={
            "title": "Netflix Subscription",
            "due_type": "subscription",
            "amount_paise": 49900,
            "due_date": "2026-12-18",
            "frequency": "monthly",
            "is_mandatory": False,
        },
        headers=auth_headers,
    )

    response = client.get("/api/v1/dues", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_list_dues_status_filter(client, auth_headers):
    client.post(
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

    response = client.get("/api/v1/dues?status=upcoming", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_update_due(client, auth_headers):
    create_resp = client.post(
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
    due_id = create_resp.json()["id"]

    response = client.patch(
        f"/api/v1/dues/{due_id}",
        json={"amount_paise": 2100000, "due_date": "2026-11-26"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["amount_paise"] == 2100000
    assert body["due_date"] == "2026-11-26"


def test_mark_due_paid(client, auth_headers):
    create_resp = client.post(
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
    due_id = create_resp.json()["id"]

    response = client.post(
        f"/api/v1/dues/{due_id}/mark-paid",
        json={"paid_date": "2026-11-25"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == due_id
    assert body["status"] == "paid"
    assert body["paid_date"] == "2026-11-25"


def test_due_not_found(client, auth_headers):
    response = client.patch(
        "/api/v1/dues/00000000-0000-0000-0000-000000000000",
        json={"amount_paise": 1000},
        headers=auth_headers,
    )
    assert response.status_code == 404

    response = client.post(
        "/api/v1/dues/00000000-0000-0000-0000-000000000000/mark-paid",
        json={"paid_date": "2026-11-25"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_dues_require_auth(client):
    response = client.get("/api/v1/dues")
    assert response.status_code == 401
