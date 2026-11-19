"""Tests for centralised error handling."""

ERROR_KEYS = {"code", "message", "details"}


def test_unknown_route_returns_contract_error(client):
    """A 404 should follow the standard error contract format."""
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert set(body["error"].keys()) == ERROR_KEYS
    assert body["error"]["code"] == "NOT_FOUND"


def test_error_response_has_no_stack_trace(client):
    """Error responses must not expose internal exception details."""
    response = client.get("/api/v1/does-not-exist")
    body = str(response.json()).lower()
    for forbidden in ["traceback", "file", "line", "sqlalchemy", "exception"]:
        assert forbidden not in body
