"""Scam detection schemas — CONTRACT.md §10."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ScamAnalyzeRequest(BaseModel):
    message: str = Field(..., description="Message to analyze for scam risk")
    source: str = Field("manual", description="Source of the message")


class IndicatorItem(BaseModel):
    code: str
    description: str


class ScamAnalyzeResponse(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="Risk score 0-100")
    risk_level: str = Field(..., description="low/medium/high/critical")
    verdict: str = Field(..., description="legitimate/suspicious/scam")
    indicators: List[IndicatorItem]
    explanation: str
    recommended_actions: List[str]


class ScamAlertItem(BaseModel):
    id: str
    message_masked: str
    risk_score: int
    risk_level: str
    verdict: str
    indicators: list
    explanation: str
    status: str
    created_at: datetime


class ScamAlertList(BaseModel):
    items: List[ScamAlertItem]
    total: int
