"""Deterministic fallback and LLM provider behaviour tests."""

from __future__ import annotations

import httpx
import json
import pytest

from app.config import Settings
from app.services.fallback_service import fallback_merchant, fallback_nudge, fallback_scam_explanation
from app.services.llm_provider import (
    DisabledLLMProvider,
    OpenAICompatibleProvider,
    build_provider,
)


def test_merchant_fallback_is_deterministic() -> None:
    first = fallback_merchant("Acme Widgets")
    second = fallback_merchant("Acme Widgets")

    assert first == second
    assert first["merchant_normalized"] == "Acme Widgets"
    assert first["category"] == "other"


def test_scam_fallback_varies_by_risk_level() -> None:
    low = fallback_scam_explanation("low", ["Unknown sender"])
    critical = fallback_scam_explanation("critical", ["Suspicious link", "UPI PIN request"])

    assert low["summary"] != critical["summary"]
    assert low["reasons"] == ["Unknown sender"]
    assert critical["reasons"] == ["Suspicious link", "UPI PIN request"]
    assert "do not open any links" in critical["safe_action"].lower()
    assert "do not open any links" not in low["safe_action"].lower()
    for body in (low, critical):
        assert "otp" in body["safe_action"].lower()
        assert "definitely" not in body["summary"].lower()


def test_scam_fallback_without_indicators_uses_generic_reason() -> None:
    result = fallback_scam_explanation("high", [])

    assert len(result["reasons"]) == 1
    assert "automated risk check" in result["reasons"][0].lower()


def test_nudge_fallback_without_facts_invents_nothing() -> None:
    result = fallback_nudge(
        category=None,
        spending_increase_percent=None,
        upcoming_due=None,
        amount_paise=None,
        days_until_due=None,
    )

    assert result["title"] == "A quick check-in"
    assert "₹" not in result["message"]
    assert not any(ch.isdigit() for ch in result["message"])


def test_nudge_fallback_uses_only_supplied_facts() -> None:
    result = fallback_nudge(
        category="food",
        spending_increase_percent=35,
        upcoming_due="Home EMI",
        amount_paise=1200000,
        days_until_due=5,
    )

    assert "Home EMI" in result["message"]
    assert "₹12,000" in result["message"]
    assert "35%" in result["message"]
    assert "5 days" in result["message"]
    assert "salary" not in result["message"].lower()


def test_nudge_fallback_due_today_and_tomorrow() -> None:
    today = fallback_nudge(
        category=None,
        spending_increase_percent=None,
        upcoming_due="Rent",
        amount_paise=None,
        days_until_due=0,
    )
    tomorrow = fallback_nudge(
        category=None,
        spending_increase_percent=None,
        upcoming_due="Rent",
        amount_paise=None,
        days_until_due=1,
    )

    assert "due today" in today["message"]
    assert "due tomorrow" in tomorrow["message"]


# --- Provider configuration -------------------------------------------------


def test_provider_none_is_disabled() -> None:
    provider = build_provider(Settings(ai_provider="none"))

    assert isinstance(provider, DisabledLLMProvider)
    assert provider.generate_json(system_prompt="s", user_prompt="u") is None


def test_unknown_provider_falls_back_to_disabled() -> None:
    provider = build_provider(Settings(ai_provider="mystery_llm"))

    assert isinstance(provider, DisabledLLMProvider)


def test_missing_credentials_disable_provider() -> None:
    provider = build_provider(Settings(ai_provider="openai", ai_api_key="", ai_model="gpt-x"))

    assert isinstance(provider, DisabledLLMProvider)


def test_configured_provider_is_enabled() -> None:
    provider = build_provider(
        Settings(ai_provider="openai", ai_api_key="test-key", ai_model="test-model")
    )

    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.enabled is True
    assert provider.name == "openai"


# --- Provider HTTP behaviour ------------------------------------------------


def _provider(handler, *, max_retries: int = 1) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        api_key="test-key",
        model="test-model",
        base_url="https://llm.example/v1",
        timeout_seconds=1.0,
        max_retries=max_retries,
        transport=httpx.MockTransport(handler),
    )


def _ok(content: str, request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def test_provider_parses_json_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _ok('{"merchant_normalized": "Netflix", "category": "entertainment"}', request)

    result = _provider(handler).generate_json(system_prompt="s", user_prompt="u")

    assert result == {"merchant_normalized": "Netflix", "category": "entertainment"}


def test_provider_parses_fenced_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _ok('```json\n{"title": "Hi"}\n```', request)

    assert _provider(handler).generate_json(system_prompt="s", user_prompt="u") == {"title": "Hi"}


def test_provider_retries_once_on_server_error() -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(500, json={"error": "boom"})
        return _ok('{"ok": true}', request)

    result = _provider(handler, max_retries=1).generate_json(system_prompt="s", user_prompt="u")

    assert calls["count"] == 2
    assert result == {"ok": True}


def test_provider_retries_are_capped_at_one() -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(503)

    result = _provider(handler, max_retries=5).generate_json(system_prompt="s", user_prompt="u")

    assert result is None
    assert calls["count"] == 2


def test_provider_does_not_retry_client_errors() -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(401)

    assert _provider(handler).generate_json(system_prompt="s", user_prompt="u") is None
    assert calls["count"] == 1


def test_provider_timeout_returns_none() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("slow provider")

    assert _provider(handler).generate_json(system_prompt="s", user_prompt="u") is None


def test_provider_invalid_json_returns_none() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _ok("this is not json", request)

    assert _provider(handler).generate_json(system_prompt="s", user_prompt="u") is None


def test_provider_uses_bearer_auth_and_configured_model() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = request.read().decode()
        return _ok('{"ok": true}', request)

    _provider(handler).generate_json(system_prompt="s", user_prompt="u")

    assert captured["auth"] == "Bearer test-key"
    body = json.loads(str(captured["body"]))
    assert body["model"] == "test-model"
    assert body["messages"][0]["role"] == "system"


@pytest.mark.parametrize("status", [400, 403, 404, 422])
def test_provider_client_error_statuses_return_none(status: int) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status)

    assert _provider(handler).generate_json(system_prompt="s", user_prompt="u") is None
