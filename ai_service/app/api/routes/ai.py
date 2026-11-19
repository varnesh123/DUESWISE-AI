"""AI API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.ai import (
    MerchantNormalizeRequest,
    MerchantNormalizeResponse,
    NudgeRequest,
    NudgeResponse,
    ScamExplainRequest,
    ScamExplanationResponse,
)
from app.services.llm_provider import LLMProvider, get_llm_provider
from app.services.merchant_service import normalize_merchant
from app.services.nudge_service import generate_nudge
from app.services.scam_service import explain_scam

router = APIRouter()


@router.post("/merchant-normalize", response_model=MerchantNormalizeResponse)
def merchant_normalize(
    payload: MerchantNormalizeRequest,
    provider: LLMProvider = Depends(get_llm_provider),
) -> MerchantNormalizeResponse:
    """Normalise a noisy merchant string and suggest a category."""

    return normalize_merchant(payload, provider)


@router.post("/explain-scam", response_model=ScamExplanationResponse)
def explain_scam_risk(
    payload: ScamExplainRequest,
    provider: LLMProvider = Depends(get_llm_provider),
) -> ScamExplanationResponse:
    """Explain a risk assessment that the deterministic backend already produced."""

    return explain_scam(payload, provider)


@router.post("/generate-nudge", response_model=NudgeResponse)
def generate_nudge_message(
    payload: NudgeRequest,
    provider: LLMProvider = Depends(get_llm_provider),
) -> NudgeResponse:
    """Word a nudge from backend-supplied financial facts."""

    return generate_nudge(payload, provider)
