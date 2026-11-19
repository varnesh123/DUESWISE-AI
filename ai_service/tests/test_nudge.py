"""Nudge generation tests."""

from __future__ import annotations

import pytest

from app.utils.money import format_inr
from tests.conftest import FakeProvider

FULL_PAYLOAD = {
    "category": "entertainment",
    "spending_increase_percent": 35,
    "upcoming_due": "Home EMI",
    "amount_paise": 1200000,
    "days_until_due": 5,
}


def _nudge(client, payload: dict):
    return client.post("/api/v1/ai/generate-nudge", json=payload)


def test_valid_context_generates_fallback_nudge(client) -> None:
    response = _nudge(client, FULL_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"title", "message", "fallback_used"}
    assert body["fallback_used"] is True
    assert "Home EMI" in body["message"]
    assert "₹12,000" in body["message"]
    assert "5 days" in body["message"]
    assert "35%" in body["message"]


def test_missing_optional_context_is_allowed(client) -> None:
    response = _nudge(client, {})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "A quick check-in"
    assert body["message"]
    assert "₹" not in body["message"]
    assert not any(ch.isdigit() for ch in body["message"])


def test_blank_optional_strings_are_treated_as_missing(client) -> None:
    response = _nudge(client, {"upcoming_due": "   ", "category": "", "days_until_due": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["fallback_used"] is True
    # A day count alone must not cause an invented due name or amount.
    assert "₹" not in body["message"]


def test_negative_days_are_rejected(client) -> None:
    response = _nudge(client, {"days_until_due": -1})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_negative_amount_is_rejected(client) -> None:
    response = _nudge(client, {"amount_paise": -100})

    assert response.status_code == 422


def test_invalid_amount_type_is_rejected(client) -> None:
    response = _nudge(client, {"amount_paise": "twelve thousand"})

    assert response.status_code == 422


def test_out_of_range_percentage_is_rejected(client) -> None:
    response = _nudge(client, {"spending_increase_percent": 5000})

    assert response.status_code == 422


def test_llm_unavailable_uses_deterministic_nudge(client_factory) -> None:
    provider = FakeProvider(payload=None)
    response = _nudge(client_factory(provider), FULL_PAYLOAD)

    assert response.status_code == 200
    assert response.json()["fallback_used"] is True
    assert len(provider.calls) == 1


def test_valid_llm_nudge_is_used(client_factory) -> None:
    provider = FakeProvider(
        payload={
            "title": "A gentle reminder",
            "message": "Your Home EMI is due in 5 days. Setting aside about ₹12,000 can keep things comfortable.",
        }
    )
    response = _nudge(client_factory(provider), FULL_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["fallback_used"] is False
    assert body["title"] == "A gentle reminder"


def test_llm_nudge_with_invented_amount_is_rejected(client_factory) -> None:
    provider = FakeProvider(
        payload={
            "title": "Heads-up",
            "message": "Your Home EMI is due in 5 days. Set aside ₹99,999 for it.",
        }
    )
    response = _nudge(client_factory(provider), FULL_PAYLOAD)

    body = response.json()
    assert body["fallback_used"] is True
    assert "99,999" not in body["message"]
    assert "₹12,000" in body["message"]


def test_llm_nudge_with_invented_due_date_numbers_is_rejected(client_factory) -> None:
    provider = FakeProvider(
        payload={
            "title": "Heads-up",
            "message": "Your Home EMI is due on 25 November 2026.",
        }
    )
    response = _nudge(client_factory(provider), FULL_PAYLOAD)

    assert response.json()["fallback_used"] is True
    assert "2026" not in response.json()["message"]


def test_llm_nudge_with_forbidden_spending_claim_is_rejected(client_factory) -> None:
    provider = FakeProvider(
        payload={
            "title": "Good news",
            "message": "You can afford this easily, so enjoy your week.",
        }
    )
    response = _nudge(client_factory(provider), FULL_PAYLOAD)

    assert response.json()["fallback_used"] is True


def test_llm_prompt_contains_only_supplied_facts(client_factory) -> None:
    provider = FakeProvider(
        payload={
            "title": "A gentle reminder",
            "message": "Your Home EMI is due in 5 days.",
        }
    )
    _nudge(client_factory(provider), FULL_PAYLOAD)

    user_prompt = provider.calls[0]["user"]
    assert "Home EMI" in user_prompt
    assert "1200000" in user_prompt
    assert "₹12,000" in user_prompt
    assert "35%" in user_prompt
    # No fabricated facts are added by prompt construction.
    assert "salary" not in user_prompt.lower()
    assert "balance" not in user_prompt.lower()


@pytest.mark.parametrize(
    ("paise", "expected"),
    [
        (0, "₹0"),
        (89900, "₹899"),
        (1200000, "₹12,000"),
        (120000000, "₹12,00,000"),
        (123456, "₹1,234.56"),
    ],
)
def test_indian_currency_formatting(paise: int, expected: str) -> None:
    assert format_inr(paise) == expected
