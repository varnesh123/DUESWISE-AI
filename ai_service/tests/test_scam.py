"""Scam explanation tests."""

from __future__ import annotations

from tests.conftest import FakeProvider

HARD_PAYLOAD = {
    "risk_score": 96,
    "risk_level": "critical",
    "indicators": ["Suspicious external link", "Requests UPI PIN"],
    "message": "Your account will be blocked. Verify at http://secure-bank.example and share your UPI PIN.",
}


def _explain(client, payload: dict):
    return client.post("/api/v1/ai/explain-scam", json=payload)


def test_high_risk_assessment_is_explained(client) -> None:
    response = _explain(client, HARD_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"summary", "reasons", "safe_action"}
    assert body["summary"]
    assert len(body["reasons"]) >= 1
    assert "do not" in body["safe_action"].lower()
    assert "otp" in body["safe_action"].lower() or "pin" in body["safe_action"].lower()


def test_low_risk_assessment_remains_cautious(client) -> None:
    response = _explain(
        client,
        {
            "risk_score": 12,
            "risk_level": "low",
            "indicators": ["Unknown sender"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "phishing" not in body["summary"].lower()
    assert body["reasons"] == ["Unknown sender"]
    assert "otp" in body["safe_action"].lower()


def test_empty_message_is_allowed(client) -> None:
    response = _explain(
        client,
        {
            "risk_score": 40,
            "risk_level": "medium",
            "indicators": [],
            "message": "",
        },
    )

    assert response.status_code == 200
    assert response.json()["summary"]


def test_response_never_returns_a_risk_score(client) -> None:
    response = _explain(client, HARD_PAYLOAD)

    body = response.json()
    assert "risk_score" not in body
    assert "risk_level" not in body
    assert "96" not in response.text


def test_missing_risk_score_is_rejected(client) -> None:
    response = _explain(client, {"risk_level": "high", "indicators": []})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_out_of_range_risk_score_is_rejected(client) -> None:
    response = _explain(client, {"risk_score": 150, "risk_level": "critical", "indicators": []})

    assert response.status_code == 422


def test_invalid_risk_level_is_rejected(client) -> None:
    response = _explain(client, {"risk_score": 50, "risk_level": "severe", "indicators": []})

    assert response.status_code == 422


def test_invalid_indicator_type_is_rejected(client) -> None:
    response = _explain(client, {"risk_score": 50, "risk_level": "high", "indicators": "link"})

    assert response.status_code == 422


def test_llm_unavailable_uses_deterministic_explanation(client) -> None:
    response = _explain(client, HARD_PAYLOAD)

    body = response.json()
    assert "strong signs" in body["summary"].lower()
    assert body["reasons"] == ["Suspicious external link", "Requests UPI PIN"]
    assert "do not open any links" in body["safe_action"].lower()


def test_llm_explanation_is_used_when_valid(client_factory) -> None:
    provider = FakeProvider(
        payload={
            "summary": "This message shows signs of a possible phishing attempt.",
            "reasons": ["It contains an unsolicited link", "It asks for your UPI PIN"],
            "safe_action": "Do not open the link. Do not share your OTP or UPI PIN with anyone.",
        }
    )
    response = _explain(client_factory(provider), HARD_PAYLOAD)

    assert response.status_code == 200
    assert response.json()["summary"].startswith("This message shows signs")
    assert len(provider.calls) == 1


def test_llm_prompt_contains_supplied_assessment_but_no_secrets(client_factory) -> None:
    provider = FakeProvider(
        payload={
            "summary": "This message shows signs of a possible phishing attempt.",
            "reasons": ["It asks for a credential"],
            "safe_action": "Do not share your OTP or PIN.",
        }
    )
    _explain(client_factory(provider), HARD_PAYLOAD)

    user_prompt = provider.calls[0]["user"]
    assert "critical" in user_prompt
    assert "96" in user_prompt
    assert "Suspicious external link" in user_prompt
    # The message text mentions a UPI PIN but contains no PIN value; ensure the
    # excerpt is present only in masked/truncated form.
    assert "secure-bank.example" in user_prompt
    assert len(user_prompt) < 2000


def test_unsafe_llm_instruction_is_rejected(client_factory) -> None:
    provider = FakeProvider(
        payload={
            "summary": "This looks suspicious.",
            "reasons": ["A link is present"],
            "safe_action": "Please share your OTP with our support team immediately.",
        }
    )
    response = _explain(client_factory(provider), HARD_PAYLOAD)

    body = response.json()
    assert "please share" not in body["safe_action"].lower()
    assert "strong signs" in body["summary"].lower()


def test_definitive_fraud_claim_is_rejected(client_factory) -> None:
    provider = FakeProvider(
        payload={
            "summary": "This message is definitely fraudulent.",
            "reasons": ["A link is present"],
            "safe_action": "Do not share your OTP or PIN.",
        }
    )
    response = _explain(client_factory(provider), HARD_PAYLOAD)

    assert "definitely fraudulent" not in response.json()["summary"].lower()


def test_credential_warning_is_appended_when_llm_omits_it(client_factory) -> None:
    provider = FakeProvider(
        payload={
            "summary": "This message shows signs of a possible phishing attempt.",
            "reasons": ["It contains an unsolicited link"],
            "safe_action": "Check your bank account through the official app.",
        }
    )
    response = _explain(client_factory(provider), HARD_PAYLOAD)

    safe_action = response.json()["safe_action"].lower()
    assert "official app" in safe_action
    assert "otp" in safe_action
