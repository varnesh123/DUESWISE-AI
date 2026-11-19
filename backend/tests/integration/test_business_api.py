"""Integration tests for business cash flow API — CONTRACT.md §12."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def auth_headers(client):
    client.post("/api/v1/auth/demo", json={"persona": "shopkeeper"})
    return {"Authorization": "Bearer 33333333-3333-4333-8333-333333333333"}


def test_cashflow_endpoint(client, auth_headers):
    response = client.get(
        "/api/v1/business/cashflow?current_cash_paise=5000000&forecast_date=2026-12-19",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["currency"] == "INR"
    assert body["current_cash_paise"] == 5000000
    assert "total_sales_paise" in body
    assert "total_expenses_paise" in body
    assert "pending_receivables_paise" in body
    assert "pending_payables_paise" in body
    assert "projected_cash_balance_paise" in body
    assert "forecast_date" in body
    assert "items" in body
    assert isinstance(body["projected_cash_balance_paise"], int)


def test_create_business_entry(client, auth_headers):
    response = client.post(
        "/api/v1/business/entries",
        json={
            "entry_type": "receivable",
            "description": "Customer invoice INV-001",
            "amount_paise": 300000,
            "due_date": "2026-11-25",
            "counterparty": "Customer A",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["entry_type"] == "receivable"
    assert body["description"] == "Customer invoice INV-001"
    assert body["amount_paise"] == 300000
    assert body["counterparty"] == "Customer A"
    assert body["status"] == "pending"
    assert "id" in body


def test_generate_invoice(client, auth_headers):
    response = client.post(
        "/api/v1/business/invoices",
        json={
            "invoice_number": "INV-001",
            "invoice_date": "2026-11-19",
            "customer_name": "Customer A",
            "customer_gstin": None,
            "items": [
                {
                    "description": "Retail goods",
                    "quantity": 2,
                    "unit_price_paise": 100000,
                    "gst_rate_basis_points": 1800,
                }
            ],
            "place_of_supply": "Tamil Nadu",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["invoice_number"] == "INV-001"
    assert body["subtotal_paise"] == 200000
    assert body["cgst_paise"] == 18000  # 9% of 200000
    assert body["sgst_paise"] == 18000
    assert body["igst_paise"] == 0
    assert body["total_paise"] == 236000
    assert body["tax_calculation_status"] == "illustrative"


def test_business_requires_auth(client):
    response = client.get("/api/v1/business/cashflow")
    assert response.status_code == 401
