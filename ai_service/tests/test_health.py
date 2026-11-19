"""Health endpoint tests."""

from __future__ import annotations

from tests.conftest import FakeProvider


def test_health_returns_ok(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["content-type"].startswith("application/json")


def test_health_works_with_llm_enabled_but_unreachable(client_factory) -> None:
    enabled_but_empty = FakeProvider(payload=None)
    response = client_factory(enabled_but_empty).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert enabled_but_empty.calls == []
