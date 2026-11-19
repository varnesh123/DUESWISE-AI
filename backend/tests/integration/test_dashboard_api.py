"""Integration tests for dashboard summary API — CONTRACT.md §4."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def auth_headers(client):
    client.post("/api/v1/auth/demo", json={"persona": "salaried"})
    return {"Authorization": "Bearer 11111111-1111-4111-8111-111111111111"}


def test_dashboard_summary(client, auth_headers):
    # Create a due so next_due is populated
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

    # Create a recent transaction
    client.post(
        "/api/v1/transactions/manual",
        json={
            "amount_paise": 5000000,
            "transaction_type": "credit",
            "merchant": "Salary Credit",
            "category": "salary",
            "payment_method": "net_banking",
            "transaction_date": "2026-11-19",
        },
        headers=auth_headers,
    )

    response = client.get(
        "/api/v1/dashboard/summary?calculation_date=2026-11-19&available_balance_paise=5000000",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["currency"] == "INR"
    assert body["available_balance_paise"] == 5000000
    assert "safe_to_spend_paise" in body
    assert "upcoming_dues_total_paise" in body
    assert "safety_reserve_paise" in body
    assert "projected_income_paise" in body
    assert body["calculated_until"] == "2026-12-19"
    assert body["calculation_date"] == "2026-11-19"
    assert body["forecast_horizon_days"] == 30
    assert body["data_confidence"] in ("low", "medium", "high")
    assert body["next_due"] is not None
    assert body["next_due"]["title"] == "Home EMI"
    assert len(body["recent_transactions"]) >= 1
    # All amounts are integers
    assert isinstance(body["safe_to_spend_paise"], int)
    assert isinstance(body["upcoming_dues_total_paise"], int)


def test_dashboard_default_date(client, auth_headers):
    """Dashboard should work with default (today) calculation date."""
    response = client.get(
        "/api/v1/dashboard/summary?available_balance_paise=5000000",
        headers=auth_headers,
    )
    assert response.status_code == 200


def test_dashboard_invalid_date(client, auth_headers):
    response = client.get(
        "/api/v1/dashboard/summary?calculation_date=not-a-date",
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_dashboard_requires_auth(client):
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 401
