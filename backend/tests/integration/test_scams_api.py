"""Integration tests for scam detection API — CONTRACT.md §10."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def auth_headers(client):
    client.post("/api/v1/auth/demo", json={"persona": "salaried"})
    return {"Authorization": "Bearer 11111111-1111-4111-8111-111111111111"}


def test_analyze_scam_urgent_link(client, auth_headers):
    response = client.post(
        "/api/v1/scams/analyze",
        json={
            "message": "Your UPI account will be blocked. Verify immediately using this link.",
            "source": "manual",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert "risk_score" in body
    assert "risk_level" in body
    assert "verdict" in body
    assert "indicators" in body
    assert "explanation" in body
    assert "recommended_actions" in body
    assert 0 <= body["risk_score"] <= 100
    assert body["verdict"] in ("legitimate", "suspicious", "scam")


def test_analyze_scam_legitimate(client, auth_headers):
    response = client.post(
        "/api/v1/scams/analyze",
        json={
            "message": "Your salary of Rs 50000 has been credited to your account.",
            "source": "manual",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["risk_score"] == 0
    assert body["verdict"] == "legitimate"


def test_list_scams(client, auth_headers):
    client.post(
        "/api/v1/scams/analyze",
        json={"message": "Your UPI account will be blocked. Verify immediately using this link.", "source": "manual"},
        headers=auth_headers,
    )

    response = client.get("/api/v1/scams", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1


def test_scams_require_auth(client):
    response = client.post("/api/v1/scams/analyze", json={"message": "test", "source": "manual"})
    assert response.status_code == 401
