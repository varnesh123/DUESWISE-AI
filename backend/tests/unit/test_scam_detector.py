"""Unit tests for scam detector."""

import pytest

from app.services.scam_detector import analyze_message, _score_level, _verdict_from_level


def test_urgent_threat():
    result = analyze_message("Your UPI account will be blocked immediately. Verify now.")
    assert result.risk_score > 0
    assert result.risk_level in ("medium", "high", "critical")
    assert any(i["code"] == "URGENT_THREAT" for i in result.indicators)


def test_suspicious_link():
    result = analyze_message("Click here: bit.ly/3xyz to verify your account.")
    assert result.risk_score > 0
    assert any(i["code"] == "SUSPICIOUS_LINK" for i in result.indicators)


def test_otp_request():
    result = analyze_message("Share your OTP to verify your account.")
    assert result.risk_score >= 30
    assert any(i["code"] == "OTP_REQUEST" for i in result.indicators)


def test_collect_request():
    result = analyze_message("Please pay now using this collect request.")
    assert any(i["code"] == "COLLECT_REQUEST" for i in result.indicators)


def test_suspicious_link_without_threat_words():
    result = analyze_message("Click here: bit.ly/3xyz to verify.")
    assert any(i["code"] == "SUSPICIOUS_LINK" for i in result.indicators)


def test_legitimate_message():
    result = analyze_message("Your salary of Rs 50000 has been credited to your account.")
    assert result.risk_score == 0
    assert result.risk_level == "low"
    assert result.verdict == "legitimate"
    assert result.indicators == []


def test_empty_message():
    result = analyze_message("")
    assert result.risk_score == 0
    assert result.verdict == "legitimate"


def test_score_level_boundaries():
    assert _score_level(0) == "low"
    assert _score_level(24) == "low"
    assert _score_level(25) == "medium"
    assert _score_level(49) == "medium"
    assert _score_level(50) == "high"
    assert _score_level(74) == "high"
    assert _score_level(75) == "critical"
    assert _score_level(100) == "critical"


def test_verdict_from_level():
    assert _verdict_from_level("critical") == "scam"
    assert _verdict_from_level("high") == "suspicious"
    assert _verdict_from_level("medium") == "suspicious"
    assert _verdict_from_level("low") == "legitimate"
