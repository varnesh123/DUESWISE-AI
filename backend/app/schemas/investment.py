"""Investment education schemas — CONTRACT.md §13."""

from typing import List
from pydantic import BaseModel, Field


class PortfolioAssetItem(BaseModel):
    asset_name: str
    asset_type: str  # equity/debt/hybrid/gold
    value_paise: int
    weight_percent: int


class InvestmentSummaryResponse(BaseModel):
    currency: str
    monthly_surplus_paise: int
    suggested_sip_paise: int
    portfolio: List[PortfolioAssetItem]
    concentration_risk: str
    educational_disclaimer: str
