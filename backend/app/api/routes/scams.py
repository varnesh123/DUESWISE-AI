"""Scam detection API routes — CONTRACT.md §10.

Risk score is calculated by backend rules. AI never overrides the score or
verdict. AI integration is optional and only used for explanation (not yet
implemented in Phase 3 — deterministic fallback always used).
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import DbSession, get_current_user
from app.models.scam_alert import ScamAlert
from app.models.user import User
from app.repositories.scam_repository import ScamRepository
from app.schemas.scam import (
    IndicatorItem,
    ScamAnalyzeRequest,
    ScamAnalyzeResponse,
    ScamAlertItem,
    ScamAlertList,
)
from app.services.scam_detector import analyze_message

router = APIRouter()


def _alert_to_item(alert: ScamAlert) -> ScamAlertItem:
    return ScamAlertItem(
        id=alert.id,
        message_masked=alert.message_masked,
        risk_score=alert.risk_score,
        risk_level=alert.risk_level,
        verdict=alert.verdict,
        indicators=alert.indicators or [],
        explanation=alert.explanation,
        status=alert.status,
        created_at=alert.created_at,
    )


@router.post(
    "/scams/analyze",
    response_model=ScamAnalyzeResponse,
    tags=["scams"],
    summary="Analyze a message for scam risk",
)
def analyze_scam(
    payload: ScamAnalyzeRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """Analyze a message for scam risk using deterministic rules.

    The backend calculates the score. AI never overrides it. The result is
    stored as a scam alert for user review.
    """
    result = analyze_message(payload.message)

    # Mask any account-like patterns before storing (privacy rule)
    import re
    masked_message = re.sub(r"\b\d{4,}\b", lambda m: "X" * (len(m.group(0)) - 4) + m.group(0)[-4:], payload.message)

    repo = ScamRepository(db)
    alert = repo.create(
        user_id=current_user.id,
        message_masked=masked_message,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        verdict=result.verdict,
        indicators=result.indicators,
        explanation=result.explanation,
        status="new",
    )

    return ScamAnalyzeResponse(
        risk_score=alert.risk_score,
        risk_level=alert.risk_level,
        verdict=alert.verdict,
        indicators=[IndicatorItem(code=i["code"], description=i["description"]) for i in result.indicators],
        explanation=result.explanation,
        recommended_actions=result.recommended_actions,
    )


@router.get(
    "/scams",
    response_model=ScamAlertList,
    tags=["scams"],
    summary="List scam alerts",
)
def list_scams(
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """List the user's scam alerts."""
    repo = ScamRepository(db)
    items, total = repo.list(user_id=current_user.id)
    return ScamAlertList(
        items=[_alert_to_item(a) for a in items],
        total=total,
    )
