"""Subscription schemas — CONTRACT.md §8."""

from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class SubscriptionItem(BaseModel):
    id: str
    merchant: str
    category: str
    expected_amount_paise: int
    frequency: str
    next_due_date: date
    detection_confidence: float
    status: str
    is_user_confirmed: bool


class SubscriptionList(BaseModel):
    items: List[SubscriptionItem]
    total: int


class SubscriptionConfirmResponse(BaseModel):
    id: str
    status: str
    is_user_confirmed: bool


class SubscriptionDismissResponse(BaseModel):
    id: str
    status: str
