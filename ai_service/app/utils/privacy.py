"""Privacy utilities: masking and redaction before any LLM prompt is built.

This module is deliberately dependency-free and side-effect free. It never logs
the content it processes.
"""

from __future__ import annotations

import re

REDACTED = "[REDACTED]"

_WHITESPACE = re.compile(r"\s+")
_ZERO_WIDTH = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
_ACCOUNT_NUMBER = re.compile(r"(?<![\d\w])\d{9,18}(?![\d\w])")
_UPI_ID = re.compile(r"(?<![\w.])([A-Za-z0-9._-]{2,})@([A-Za-z][A-Za-z0-9.]{1,})(?![\w.])")
_PHONE_NUMBER = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?([6-9]\d{9})(?!\d)")

_SECRET_CONTEXT = re.compile(
    r"(?i)\b(otp|o\.t\.p\.?|one[\s-]?time[\s-]?password|upi[\s-]?pin|pin|password|passcode|cvv|"
    r"card[\s-]?number|account[\s-]?number)\b"
    r"(\s*(?:is|was|:|=|-)?\s*)"
    r"([A-Za-z0-9@#$%^&*!._/-]{3,})"
)

# Words that commonly follow a credential keyword but are not secret values.
_NOT_A_SECRET = {
    "is",
    "was",
    "request",
    "requests",
    "requested",
    "asking",
    "asked",
    "required",
    "requirement",
    "entry",
    "field",
    "verification",
    "verify",
    "reset",
    "change",
    "update",
    "sharing",
    "exposure",
}

_ALWAYS_SECRET_KEYWORDS = {"password", "passcode", "cvv"}


def _mask_value(value: str, keep_last: int = 4) -> str:
    if len(value) <= keep_last:
        return "*" * len(value)
    return "*" * (len(value) - keep_last) + value[-keep_last:]


def mask_account_numbers(text: str) -> str:
    """Mask 9-18 digit account/Aadhaar style identifiers, keeping the last four."""

    if not text:
        return ""

    def _replace(match: re.Match[str]) -> str:
        return _mask_value(match.group(0), keep_last=4)

    return _ACCOUNT_NUMBER.sub(_replace, text)


def mask_phone_numbers(text: str) -> str:
    """Mask Indian mobile numbers, keeping the last four digits."""

    if not text:
        return ""

    def _replace(match: re.Match[str]) -> str:
        return "******" + match.group(1)[-4:]

    return _PHONE_NUMBER.sub(_replace, text)


def mask_upi_ids(text: str) -> str:
    """Mask UPI handles while preserving the payment-handle domain."""

    if not text:
        return ""

    def _replace(match: re.Match[str]) -> str:
        prefix = match.group(1)
        visible = prefix[:2] if len(prefix) > 2 else prefix[:1]
        return f"{visible}***@{match.group(2)}"

    return _UPI_ID.sub(_replace, text)


def redact_secrets(text: str) -> str:
    """Replace OTPs, PINs, passwords and similar secret values with a marker.

    Credential words themselves are preserved so safety explanations remain
    readable; only the supplied value is removed.
    """

    if not text:
        return ""

    def _replace(match: re.Match[str]) -> str:
        keyword = match.group(1)
        separator = match.group(2)
        value = match.group(3)
        if value.lower() in _NOT_A_SECRET and keyword.lower() not in _ALWAYS_SECRET_KEYWORDS:
            return match.group(0)
        if keyword.lower() not in _ALWAYS_SECRET_KEYWORDS and not any(ch.isdigit() for ch in value):
            return match.group(0)
        return f"{keyword}{separator}{REDACTED}"

    return _SECRET_CONTEXT.sub(_replace, text)


def mask_pii(text: str) -> str:
    """Apply secret redaction and PII masking in a safe order."""

    if not text:
        return ""
    masked = redact_secrets(text)
    masked = mask_upi_ids(masked)
    masked = mask_phone_numbers(masked)
    masked = mask_account_numbers(masked)
    return masked


def sanitize_for_llm(text: str | None, *, max_chars: int = 600) -> str:
    """Normalise, mask and truncate untrusted text before prompt construction."""

    if not text:
        return ""
    cleaned = "".join(ch if (ch.isprintable() or ch in " \n\t") else " " for ch in text)
    cleaned = _ZERO_WIDTH.sub("", cleaned)
    cleaned = _WHITESPACE.sub(" ", cleaned).strip()
    cleaned = mask_pii(cleaned)
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rstrip() + "…"
    return cleaned


def contains_sensitive_secret(text: str) -> bool:
    """Return True when the text contains a credential value or identifier we mask."""

    if not text:
        return False
    return mask_pii(text) != text
