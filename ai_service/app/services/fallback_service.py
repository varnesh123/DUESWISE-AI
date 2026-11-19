"""Deterministic templates used whenever the LLM is unavailable or unsafe.

These functions never invent financial facts and never make definitive fraud
claims. They are the guaranteed behaviour of the service with
``AI_PROVIDER=none``.
"""

from __future__ import annotations

from app.utils.money import format_inr

_LEVEL_SUMMARY = {
    "low": "This message has a few minor warning signs, so it is worth a quick check.",
    "medium": "This message shows some warning signs that deserve caution.",
    "high": "This message shows several signs of a possible phishing attempt.",
    "critical": "This message shows strong signs of a phishing attempt and should be treated as unsafe.",
}

_LEVEL_GENERIC_REASON = {
    "low": "An automated risk check flagged a small number of indicators.",
    "medium": "An automated risk check flagged indicators that are common in fraudulent messages.",
    "high": "An automated risk check flagged multiple indicators that are common in phishing messages.",
    "critical": "An automated risk check flagged strong indicators that are common in phishing messages.",
}

_SAFE_ACTION_BASE = (
    "Do not share your OTP, UPI PIN, password or card details with anyone. "
    "Confirm the request through your bank's official app or verified customer-care number."
)
_SAFE_ACTION_STRONG_PREFIX = "Do not open any links or call numbers in this message. "


def fallback_merchant(display_name: str) -> dict:
    """Return a readable best-effort merchant name with low confidence."""

    name = display_name.strip() or "Unknown merchant"
    if len(name) > 80:
        name = name[:80].rstrip()
    confidence = 0.2 if name == "Unknown merchant" else 0.35
    return {
        "merchant_normalized": name,
        "canonical_name": name,
        "category": "other",
        "confidence": confidence,
    }


def fallback_scam_explanation(risk_level: str, indicators: list[str]) -> dict:
    """Build a cautious explanation from the supplied deterministic assessment."""

    level = risk_level if risk_level in _LEVEL_SUMMARY else "medium"
    reasons = [indicator.strip()[:160] for indicator in indicators if indicator.strip()][:4]
    if not reasons:
        reasons = [_LEVEL_GENERIC_REASON[level]]

    safe_action = _SAFE_ACTION_BASE
    if level in {"high", "critical"}:
        safe_action = _SAFE_ACTION_STRONG_PREFIX + safe_action

    return {
        "summary": _LEVEL_SUMMARY[level],
        "reasons": reasons,
        "safe_action": safe_action,
    }


def _due_phrase(days_until_due: int | None) -> str | None:
    if days_until_due is None:
        return None
    if days_until_due == 0:
        return "today"
    if days_until_due == 1:
        return "tomorrow"
    return f"in {days_until_due} days"


def _fallback_title(
    *,
    upcoming_due: str | None,
    category: str | None,
    spending_increase_percent: int | None,
) -> str:
    if upcoming_due:
        return "Upcoming payment reminder"
    if spending_increase_percent is not None and (category or spending_increase_percent > 0):
        return "A small heads-up"
    return "A quick check-in"


def fallback_nudge(
    *,
    category: str | None,
    spending_increase_percent: int | None,
    upcoming_due: str | None,
    amount_paise: int | None,
    days_until_due: int | None,
) -> dict:
    """Compose a deterministic, fact-only nudge from backend-supplied context."""

    sentences: list[str] = []

    if upcoming_due:
        when = _due_phrase(days_until_due)
        if when and amount_paise is not None:
            sentences.append(
                f"Your {upcoming_due} is due {when}. "
                f"Setting aside about {format_inr(amount_paise)} beforehand can make it easier to manage."
            )
        elif when:
            sentences.append(
                f"Your {upcoming_due} is due {when}. "
                "A quick look at your balance now can help you plan for it."
            )
        elif amount_paise is not None:
            sentences.append(
                f"Your {upcoming_due} is coming up. "
                f"Keeping about {format_inr(amount_paise)} aside can make it easier to manage."
            )
        else:
            sentences.append(
                f"Your {upcoming_due} is coming up. A quick look at your upcoming payments can help you plan."
            )

    if spending_increase_percent is not None and spending_increase_percent > 0:
        label = category.strip().capitalize() if category and category.strip() else "Your"
        if label == "Your":
            sentences.append(
                f"Your spending is up about {spending_increase_percent}% compared with your usual pattern. "
                "A quick review of recent payments could help you stay on track."
            )
        else:
            sentences.append(
                f"{label} spending is up about {spending_increase_percent}% compared with your usual pattern. "
                "A quick review of recent payments could help you stay on track."
            )

    if not sentences:
        sentences.append(
            "You have a moment to check your recent spending and upcoming payments. "
            "Small check-ins like this can help you stay on track."
        )

    message = " ".join(sentences)
    if len(message) > 500:
        message = message[:497].rstrip() + "…"

    return {
        "title": _fallback_title(
            upcoming_due=upcoming_due,
            category=category,
            spending_increase_percent=spending_increase_percent,
        ),
        "message": message,
    }
