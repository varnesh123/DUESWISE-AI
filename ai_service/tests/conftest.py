"""Shared pytest fixtures.

Tests never contact a real LLM provider: every test runs against the
deterministic provider or an in-memory fake whose calls can be inspected.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.llm_provider import DisabledLLMProvider, get_llm_provider


class FakeProvider:
    """Deterministic LLM stub that records prompts instead of calling the network."""

    enabled = True
    name = "fake"

    def __init__(self, payload: dict | None = None) -> None:
        self.payload = payload
        self.calls: list[dict[str, str]] = []

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict | None:
        self.calls.append({"system": system_prompt, "user": user_prompt})
        return dict(self.payload) if self.payload is not None else None


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def client_factory() -> Iterator[Callable[..., TestClient]]:
    created: list[TestClient] = []

    def _factory(provider=None) -> TestClient:
        application = create_app()
        overridden = provider or DisabledLLMProvider()
        application.dependency_overrides[get_llm_provider] = lambda: overridden
        client = TestClient(application)
        created.append(client)
        return client

    yield _factory
    for client in created:
        client.close()


@pytest.fixture
def client(client_factory) -> TestClient:
    return client_factory()
