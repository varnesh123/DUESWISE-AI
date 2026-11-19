"""Integration tests for tax comparison API — CONTRACT.md §11."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def auth_headers(client):
    client.post("/api/v1/auth/demo", json={"persona": "salaried"})
    return {"Authorization": "Bearer 11111111-1111-4111-8111-111111111111"}


def test_compare_tax_regimes(client, auth_headers):
    response = client.post(
        "/api/v1/tax/compare",
        json={
            "financial_year": "FY-2025-26",
            "annual_salary_paise": 12000000,
            "deductions": {
                "section_80c_paise": 1500000,
                "section_80d_paise": 250000,
                "section_80ccd_1b_paise": 500000,
                "hra_exemption_paise": 0,
                "home_loan_interest_paise": 0,
                "other_eligible_deductions_paise": 0,
            },
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["financial_year"] == "FY-2025-26"
    assert body["gross_salary_paise"] == 12000000
    assert "old_regime" in body
    assert "new_regime" in body
    assert body["lower_tax_regime"] in ("old", "new")
    assert body["estimated_savings_paise"] >= 0
    assert "not professional tax advice" in body["disclaimer"]
    assert "rules_metadata" in body
    assert body["rules_metadata"]["verification_status"] == "unverified"
    # All paise fields are integers
    assert isinstance(body["old_regime"]["total_tax_paise"], int)
    assert isinstance(body["new_regime"]["total_tax_paise"], int)


def test_compare_tax_unsupported_year(client, auth_headers):
    response = client.post(
        "/api/v1/tax/compare",
        json={
            "financial_year": "FY-2024-25",
            "annual_salary_paise": 1200000,
            "deductions": {},
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_tax_requires_auth(client):
    response = client.post("/api/v1/tax/compare", json={"financial_year": "FY-2025-26", "annual_salary_paise": 1000000, "deductions": {}})
    assert response.status_code == 401
