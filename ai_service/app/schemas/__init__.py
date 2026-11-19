"""AI service request and response schemas."""

from app.schemas.ai import (
    ErrorBody,
    ErrorResponse,
    LLMMerchantOutput,
    LLMNudgeOutput,
    LLMScamOutput,
    MerchantCategory,
    MerchantNormalizeRequest,
    MerchantNormalizeResponse,
    NudgeRequest,
    NudgeResponse,
    RiskLevel,
    ScamExplainRequest,
    ScamExplanationResponse,
)

__all__ = [
    "ErrorBody",
    "ErrorResponse",
    "LLMMerchantOutput",
    "LLMNudgeOutput",
    "LLMScamOutput",
    "MerchantCategory",
    "MerchantNormalizeRequest",
    "MerchantNormalizeResponse",
    "NudgeRequest",
    "NudgeResponse",
    "RiskLevel",
    "ScamExplainRequest",
    "ScamExplanationResponse",
]
