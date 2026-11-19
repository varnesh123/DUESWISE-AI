"""Tests for the health endpoint."""

def test_health_returns_ok(client):
    """GET /health should return a success response."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_application_imports_and_starts():
    """The FastAPI application object can be imported and instantiated."""
    from app.main import app

    assert app is not None
    assert app.title == "DuesWise"
