"""Nudge wording generation.

The backend decides whether a nudge is eligible. This service only words the
nudge using facts supplied by the backend, and never invents financial values.
"""

from __future__ import annotations

import re

from app.schemas.ai import LLMNudgeOutput, NudgeRequest, NudgeResponse
from app.services.fallback_service import fallback_nudge
from app.services.llm_provider import LLMProvider
from app.utils.money import format_inr
from app.utils.privacy import sanitize_for_llm

NUDGE_SYSTEM_PROMPT = (
    "You write short, calm, respectful nudges for an Indian personal finance app. "
    "The app's deterministic engine has already decided that a nudge is appropriate. "
    "Use only the facts provided. Never invent, estimate or change income, spending, balances, "
    "amounts, due dates or percentages. Never suggest that money is available to spend, and never "
    "recommend borrowing or investing. Avoid fear, shame, urgency or pressure. "
    "Reply with JSON only, using exactly these keys: "
    '{"title": string, "message": string}. '
    "title must be under 120 characters and message under 500 characters. "
    "Write in simple English and use at most two short sentences in the message."
)

_FORBIDDEN_PHRASES = re.compile(
    r"\b(safe to spend|you can afford|guaranteed|risk[- ]free|invest now|borrow now)\b",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\d[\d,]*")


def _allowed_numbers(request: NudgeRequest) -> set[str]:
    allowed: set[str] = set()
    if request.amount_paise is not None:
        allowed.add(str(request.amount_paise))
        allowed.add(str(request.amount_paise // 100))
        allowed.add(format_inr(request.amount_paise).replace("₹", "").replace(",", ""))
    if request.spending_increase_percent is not None:
        allowed.add(str(request.spending_increase_percent))
    if request.days_until_due is not None:
        allowed.add(str(request.days_until_due))
    return allowed


def _has_unexpected_numbers(text: str, allowed: set[str]) -> bool:
    for raw in _NUMBER.findall(text or ""):
        token = raw.replace(",", "").lstrip("0") or "0"
        if token not in allowed:
            return True
    return False


def build_nudge_prompt(request: NudgeRequest) -> tuple[str, str]:
    """Build masked prompts containing only backend-supplied facts."""

    facts: list[str] = []
    if request.upcoming_due:
        facts.append(f"Upcoming due: {sanitize_for_llm(request.upcoming_due, max_chars=80)}")
    if request.days_until_due is not None:
        facts.append(f"Days until due: {request.days_until_due}")
    if request.amount_paise is not None:
        facts.append(
            f"Amount: {format_inr(request.amount_paise)} ({request.amount_paise} paise)"
        )
    if request.category:
        facts.append(f"Category: {sanitize_for_llm(request.category, max_chars=40)}")
    if request.spending_increase_percent is not None:
        facts.append(f"Spending increase versus the user's usual pattern: {request.spending_increase_percent}%")
    if not facts:
        facts.append("No specific financial facts were provided.")
    facts.append("Word a brief, supportive nudge using only these facts.")
    return NUDGE_SYSTEM_PROMPT, "\n".join(facts)


def _llm_nudge(request: NudgeRequest, provider: LLMProvider) -> NudgeResponse | None:
    if not provider.enabled:
        return None

    system_prompt, user_prompt = build_nudge_prompt(request)
    payload = provider.generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
    if not payload:
        return None

    try:
        parsed = LLMNudgeOutput.model_validate(payload)
    except Exception:  # noqa: BLE001 - invalid model output is a normal fallback path
        return None

    combined = f"{parsed.title} {parsed.message}"
    if _FORBIDDEN_PHRASES.search(combined):
        return None
    if _has_unexpected_numbers(parsed.message, _allowed_numbers(request)):
        return None

    return NudgeResponse(title=parsed.title.strip(), message=parsed.message.strip(), fallback_used=False)


def generate_nudge(request: NudgeRequest, provider: LLMProvider) -> NudgeResponse:
    """Generate nudge wording from backend facts, with a deterministic fallback."""

    llm_result = _llm_nudge(request, provider)
    if llm_result is not None:
        return llm_result

    fallback = fallback_nudge(
        category=request.category,
        spending_increase_percent=request.spending_increase_percent,
        upcoming_due=request.upcoming_due,
        amount_paise=request.amount_paise,
        days_until_due=request.days_until_due,
    )
    return NudgeResponse(**fallback, fallback_used=True)
