"""Integration tests for nudges API — CONTRACT.md §9."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def auth_headers(client):
    client.post("/api/v1/auth/demo", json={"persona": "salaried"})
    return {"Authorization": "Bearer 11111111-1111-4111-8111-111111111111"}


def test_list_nudges_empty(client, auth_headers):
    response = client.get("/api/v1/nudges", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0


def test_nudge_read_dismiss_not_found(client, auth_headers):
    response = client.post(
        "/api/v1/nudges/00000000-0000-0000-0000-000000000000/read",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 404

    response = client.post(
        "/api/v1/nudges/00000000-0000-0000-0000-000000000000/dismiss",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_nudges_require_auth(client):
    response = client.get("/api/v1/nudges")
    assert response.status_code == 401
