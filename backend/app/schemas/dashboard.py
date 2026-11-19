"""Dashboard summary schema — safe-to-spend dashboard (CONTRACT.md §4)."""

from typing import Optional
from pydantic import BaseModel


class NextDueItem(BaseModel):
    id: str
    title: str
    amount_paise: int
    due_date: str


class DashboardSummaryResponse(BaseModel):
    currency: str
    available_balance_paise: int
    safe_to_spend_paise: int
    upcoming_dues_total_paise: int
    safety_reserve_paise: int
    projected_income_paise: int
    calculated_until: str
    calculation_date: str
    forecast_horizon_days: int
    data_confidence: str
    next_due: Optional[NextDueItem] = None
    recent_transactions: list = []
