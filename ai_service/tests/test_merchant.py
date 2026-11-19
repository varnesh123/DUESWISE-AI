"""Merchant normalisation tests."""

from __future__ import annotations

from tests.conftest import FakeProvider


def _normalize(client, merchant_raw: str):
    return client.post(
        "/api/v1/ai/merchant-normalize",
        json={"merchant_raw": merchant_raw, "currency": "INR"},
    )


def test_known_merchant_is_resolved_locally(client) -> None:
    response = _normalize(client, "NETFLIX INDIA PVT LTD")

    assert response.status_code == 200
    body = response.json()
    assert body["merchant_normalized"] == "Netflix"
    assert body["canonical_name"] == "Netflix"
    assert body["category"] == "entertainment"
    assert body["confidence"] >= 0.9
    assert body["fallback_used"] is False


def test_noisy_transaction_string_is_cleaned(client) -> None:
    response = _normalize(client, "UPI/SWIGGY/123456789012/12-11-2026")

    assert response.status_code == 200
    body = response.json()
    assert body["merchant_normalized"] == "Swiggy"
    assert body["category"] == "food"
    assert body["fallback_used"] is False


def test_merchant_with_trailing_corporate_suffixes(client) -> None:
    response = _normalize(client, "BIGBASKET INNOVATIVE RETAIL PRIVATE LIMITED")

    assert response.status_code == 200
    assert response.json()["merchant_normalized"] == "BigBasket"
    assert response.json()["category"] == "groceries"


def test_unknown_merchant_uses_deterministic_fallback(client) -> None:
    response = _normalize(client, "ACME WIDGETS")

    assert response.status_code == 200
    body = response.json()
    assert body["merchant_normalized"] == "Acme Widgets"
    assert body["category"] == "other"
    assert body["confidence"] < 0.5
    assert body["fallback_used"] is True


def test_empty_merchant_is_rejected(client) -> None:
    response = _normalize(client, "   ")

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "errors" in body["error"]["details"]


def test_invalid_field_types_are_rejected(client) -> None:
    response = client.post("/api/v1/ai/merchant-normalize", json={"merchant_raw": 12345})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_overlong_merchant_is_rejected(client) -> None:
    response = _normalize(client, "A" * 201)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_missing_body_is_rejected(client) -> None:
    response = client.post("/api/v1/ai/merchant-normalize")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_known_merchant_does_not_call_the_llm(client_factory) -> None:
    provider = FakeProvider(payload={"merchant_normalized": "Wrong", "category": "other", "confidence": 0.1})
    response = _normalize(client_factory(provider), "NETFLIX")

    assert response.json()["merchant_normalized"] == "Netflix"
    assert provider.calls == []


def test_unknown_merchant_uses_llm_when_enabled(client_factory) -> None:
    provider = FakeProvider(
        payload={"merchant_normalized": "Sri Lakshmi Stores", "category": "groceries", "confidence": 0.82}
    )
    response = _normalize(client_factory(provider), "SRI LAKSHMI STORES AND PROVISIONS")

    assert response.status_code == 200
    body = response.json()
    assert body["merchant_normalized"] == "Sri Lakshmi Stores"
    assert body["category"] == "groceries"
    assert body["fallback_used"] is False
    assert len(provider.calls) == 1


def test_invalid_llm_merchant_output_falls_back(client_factory) -> None:
    provider = FakeProvider(payload={"merchant_normalized": "Acme", "category": "miscellaneous", "confidence": 2})
    response = _normalize(client_factory(provider), "ACME WIDGETS")

    assert response.status_code == 200
    body = response.json()
    assert body["fallback_used"] is True
    assert body["category"] == "other"


def test_llm_unavailable_falls_back_deterministically(client_factory) -> None:
    provider = FakeProvider(payload=None)
    response = _normalize(client_factory(provider), "ACME WIDGETS")

    assert response.status_code == 200
    assert response.json()["fallback_used"] is True


def test_llm_merchant_output_cannot_echo_identifiers(client_factory) -> None:
    provider = FakeProvider(
        payload={
            "merchant_normalized": "Account 123456789012",
            "category": "other",
            "confidence": 0.9,
        }
    )
    response = _normalize(client_factory(provider), "SOME UNKNOWN VENDOR")

    body = response.json()
    assert body["fallback_used"] is True
    assert "123456789012" not in body["merchant_normalized"]
