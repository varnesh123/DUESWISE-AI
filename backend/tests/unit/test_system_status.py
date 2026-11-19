"""Tests for the system status endpoint."""

EXPECTED_KEYS = {"name", "version", "environment", "database"}


def test_system_status_structure(client):
    """GET /api/v1/system/status should return the documented structure."""
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == EXPECTED_KEYS
    assert body["name"] == "DuesWise"
    assert body["version"] == "1.0.0"
    assert body["environment"] == "development"
    assert body["database"] == "ok"


def test_system_status_no_secrets(client):
    """The system status must not expose secrets or filesystem paths."""
    response = client.get("/api/v1/system/status")
    body = response.json()
    payload = str(body).lower()
    for forbidden in ["secret", "password", "key", "token", "://", "c:\\", "/"]:
        if forbidden == "://":
            continue
        assert forbidden not in payload
