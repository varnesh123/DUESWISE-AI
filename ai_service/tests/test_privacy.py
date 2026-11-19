"""Privacy and masking tests."""

from __future__ import annotations

import logging

from app.services.nudge_service import build_nudge_prompt
from app.services.scam_service import build_scam_prompt
from app.schemas.ai import NudgeRequest
from app.utils.privacy import (
    contains_sensitive_secret,
    mask_account_numbers,
    mask_phone_numbers,
    mask_upi_ids,
    sanitize_for_llm,
)
from tests.conftest import FakeProvider

ACCOUNT = "123456789012"
OTP = "482913"


def test_account_number_masking() -> None:
    masked = mask_account_numbers(f"My account is {ACCOUNT}")

    assert ACCOUNT not in masked
    assert masked.endswith("9012")
    assert "*" in masked


def test_phone_number_masking() -> None:
    masked = mask_phone_numbers("Call +91 9876543210 now")

    assert "9876543210" not in masked
    assert "3210" in masked


def test_upi_id_masking() -> None:
    masked = mask_upi_ids("Paid to varun@okhdfcbank")

    assert "varun" not in masked
    assert "okhdfcbank" in masked
    assert "***@" in masked


def test_otp_and_pin_values_are_redacted() -> None:
    sanitized = sanitize_for_llm(f"Your OTP is {OTP} and your PIN is 7788")

    assert OTP not in sanitized
    assert "7788" not in sanitized
    assert "OTP" in sanitized
    assert "REDACTED" in sanitized


def test_credential_keywords_without_values_are_not_mangled() -> None:
    sanitized = sanitize_for_llm("The message contains a UPI PIN request")

    assert "PIN request" in sanitized


def test_password_value_is_redacted() -> None:
    sanitized = sanitize_for_llm("Your password is hunter2")

    assert "hunter2" not in sanitized


def test_contains_sensitive_secret_detection() -> None:
    assert contains_sensitive_secret(f"OTP is {OTP}")
    assert contains_sensitive_secret(f"Account number {ACCOUNT}")
    assert contains_sensitive_secret("Write to varun@okhdfcbank")
    assert not contains_sensitive_secret("Please do not share your OTP or PIN")


def test_scam_prompt_excludes_sensitive_identifiers() -> None:
    excerpt = sanitize_for_llm(
        f"Your account {ACCOUNT} will be blocked. Share OTP {OTP} and UPI PIN 7788.",
        max_chars=600,
    )
    system_prompt, user_prompt = build_scam_prompt(
        risk_score=96,
        risk_level="critical",
        indicators=["Suspicious link"],
        message_excerpt=excerpt,
    )

    combined = f"{system_prompt}\n{user_prompt}"
    assert ACCOUNT not in combined
    assert OTP not in combined
    assert "7788" not in combined
    assert "untrusted" in combined.lower()


def test_nudge_prompt_excludes_sensitive_identifiers() -> None:
    request = NudgeRequest(
        category="food varun@okhdfcbank",
        upcoming_due=f"Card {ACCOUNT}",
        amount_paise=1200000,
        days_until_due=5,
    )
    system_prompt, user_prompt = build_nudge_prompt(request)

    combined = f"{system_prompt}\n{user_prompt}"
    assert ACCOUNT not in combined
    assert "varun" not in combined


def test_request_content_is_not_written_to_logs(client, caplog) -> None:
    caplog.set_level(logging.INFO)

    response = client.post(
        "/api/v1/ai/explain-scam",
        json={
            "risk_score": 96,
            "risk_level": "critical",
            "indicators": ["Link in message"],
            "message": f"Your account {ACCOUNT} will be blocked. Share OTP {OTP} now.",
        },
    )

    assert response.status_code == 200
    assert OTP not in caplog.text
    assert ACCOUNT not in caplog.text
    assert "blocked" not in caplog.text


def test_validation_errors_do_not_echo_credentials(client) -> None:
    response = client.post(
        "/api/v1/ai/explain-scam",
        json={
            "risk_score": f"not-a-number-{OTP}",
            "risk_level": "critical",
            "indicators": [],
        },
    )

    assert response.status_code == 422
    assert OTP not in response.text


def test_llm_prompts_do_not_contain_secrets(client_factory) -> None:
    provider = FakeProvider(payload=None)
    client_factory(provider).post(
        "/api/v1/ai/explain-scam",
        json={
            "risk_score": 80,
            "risk_level": "high",
            "indicators": [f"Account {ACCOUNT}"],
            "message": f"Send OTP {OTP} to verify.",
        },
    )

    combined = " ".join(f"{call['system']} {call['user']}" for call in provider.calls)
    assert ACCOUNT not in combined
    assert OTP not in combined
