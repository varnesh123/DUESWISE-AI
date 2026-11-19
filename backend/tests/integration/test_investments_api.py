"""Integration tests for investment education API — CONTRACT.md §13."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def auth_headers(client):
    client.post("/api/v1/auth/demo", json={"persona": "salaried"})
    return {"Authorization": "Bearer 11111111-1111-4111-8111-111111111111"}


def test_investment_summary(client, auth_headers):
    response = client.get(
        "/api/v1/investments/summary?monthly_income_paise=10000000&mandatory_monthly_dues_paise=5000000&essential_monthly_expenses_paise=3000000",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["currency"] == "INR"
    assert body["monthly_surplus_paise"] == 2000000
    assert body["suggested_sip_paise"] == 400000
    assert "portfolio" in body
    assert len(body["portfolio"]) == 2
    assert body["concentration_risk"] in ("low", "medium", "high")
    assert "educational_disclaimer" in body
    assert "not an investment recommendation" in body["educational_disclaimer"].lower()
    # All paise fields are integers
    for asset in body["portfolio"]:
        assert isinstance(asset["value_paise"], int)
        assert isinstance(asset["weight_percent"], int)


def test_investment_zero_surplus(client, auth_headers):
    response = client.get(
        "/api/v1/investments/summary?monthly_income_paise=5000000&mandatory_monthly_dues_paise=5000000&essential_monthly_expenses_paise=0",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["monthly_surplus_paise"] == 0
    assert body["suggested_sip_paise"] == 0


def test_investment_requires_auth(client):
    response = client.get("/api/v1/investments/summary")
    assert response.status_code == 401
