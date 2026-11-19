"""Pydantic schemas for the AI service public API.

Field names follow CONTRACTS.md (snake_case). Where CONTRACTS.md and
BLUEPRINT.md disagree on a field name, both documented names are returned so
neither consumer breaks; see README for details.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MerchantCategory = Literal[
    "food",
    "groceries",
    "entertainment",
    "transport",
    "shopping",
    "utilities",
    "healthcare",
    "education",
    "travel",
    "finance",
    "other",
]

RiskLevel = Literal["low", "medium", "high", "critical"]

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _clean_optional(value: str | None, *, max_length: int) -> str | None:
    if value is None:
        return None
    cleaned = _CONTROL_CHARS.sub("", value).strip()
    if not cleaned:
        return None
    return cleaned[:max_length]


class MerchantNormalizeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    merchant_raw: str = Field(min_length=1, max_length=200)
    currency: str = Field(default="INR", min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")

    @field_validator("merchant_raw")
    @classmethod
    def _validate_merchant_raw(cls, value: str) -> str:
        cleaned = _CONTROL_CHARS.sub(" ", value).strip()
        if not cleaned:
            raise ValueError("merchant_raw must contain visible characters")
        if not any(ch.isalnum() for ch in cleaned):
            raise ValueError("merchant_raw must contain letters or digits")
        return cleaned

    @field_validator("currency")
    @classmethod
    def _normalise_currency(cls, value: str) -> str:
        return value.upper()


class MerchantNormalizeResponse(BaseModel):
    merchant_normalized: str
    canonical_name: str
    category: MerchantCategory
    confidence: float = Field(ge=0.0, le=1.0)
    fallback_used: bool


class ScamExplainRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    indicators: list[str] = Field(default_factory=list, max_length=20)
    message: str | None = Field(default=None, max_length=2000)

    @field_validator("indicators")
    @classmethod
    def _clean_indicators(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            text = _CONTROL_CHARS.sub(" ", value).strip()
            if text:
                cleaned.append(text[:200])
        return cleaned[:12]

    @field_validator("message")
    @classmethod
    def _clean_message(cls, value: str | None) -> str | None:
        return _clean_optional(value, max_length=2000)


class ScamExplanationResponse(BaseModel):
    summary: str
    reasons: list[str]
    safe_action: str


class NudgeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    category: str | None = Field(default=None, max_length=50)
    spending_increase_percent: int | None = Field(default=None, ge=0, le=1000)
    upcoming_due: str | None = Field(default=None, max_length=100)
    amount_paise: int | None = Field(default=None, ge=0, le=10**12)
    days_until_due: int | None = Field(default=None, ge=0, le=365)

    @field_validator("category", "upcoming_due")
    @classmethod
    def _clean_text(cls, value: str | None) -> str | None:
        return _clean_optional(value, max_length=100)


class NudgeResponse(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=500)
    fallback_used: bool


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorBody


class LLMMerchantOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    merchant_normalized: str = Field(min_length=1, max_length=80)
    category: MerchantCategory
    confidence: float = Field(ge=0.0, le=1.0)


class LLMScamOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    summary: str = Field(min_length=1, max_length=300)
    reasons: list[str] = Field(min_length=1, max_length=5)
    safe_action: str = Field(min_length=1, max_length=300)


class LLMNudgeOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=500)
