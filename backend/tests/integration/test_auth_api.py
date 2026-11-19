"""Integration tests for auth endpoints — CONTRACT.md §3."""

from fastapi.testclient import TestClient

from app.main import app


def test_demo_session_salaried(client):
    response = client.post("/api/v1/auth/demo", json={"persona": "salaried"})
    assert response.status_code == 200
    body = response.json()
    assert "user" in body
    assert body["user"]["id"] == "11111111-1111-4111-8111-111111111111"
    assert body["user"]["name"] == "Aarav Sharma"
    assert body["user"]["persona"] == "salaried"
    assert body["user"]["currency"] == "INR"
    assert body["access_token"] == "11111111-1111-4111-8111-111111111111"
    assert body["token_type"] == "bearer"


def test_demo_session_young_professional(client):
    response = client.post("/api/v1/auth/demo", json={"persona": "young_professional"})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["persona"] == "young_professional"
    assert body["user"]["id"] == "22222222-2222-4222-8222-222222222222"


def test_demo_session_shopkeeper(client):
    response = client.post("/api/v1/auth/demo", json={"persona": "shopkeeper"})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["persona"] == "shopkeeper"
    assert body["user"]["id"] == "33333333-3333-4333-8333-333333333333"


def test_demo_session_unknown_persona(client):
    response = client.post("/api/v1/auth/demo", json={"persona": "unknown"})
    assert response.status_code == 400


def test_auth_me_with_token(client):
    # First create a session
    client.post("/api/v1/auth/demo", json={"persona": "salaried"})
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer 11111111-1111-4111-8111-111111111111"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "11111111-1111-4111-8111-111111111111"
    assert body["name"] == "Aarav Sharma"


def test_auth_me_without_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_auth_me_with_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
