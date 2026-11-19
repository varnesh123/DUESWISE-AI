"""Educational investment and SIP guidance — blueprint §7 Phase 3.

Educational only. Never places orders or executes trades.

Indicative SIP suggestion:

    monthly_surplus_paise =
    monthly_income_paise
    - mandatory_monthly_dues_paise
    - essential_monthly_expenses_paise

    suggested_sip_paise = min(
        max(0, monthly_surplus_paise * 0.20),
        monthly_surplus_paise * 0.50
    )

Concentration risk assessed using mock portfolio weights.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class PortfolioAsset:
    asset_name: str
    asset_type: str  # equity/debt/hybrid/gold
    value_paise: int
    weight_percent: int


@dataclass
class InvestmentSummary:
    currency: str
    monthly_surplus_paise: int
    suggested_sip_paise: int
    portfolio: List[PortfolioAsset]
    concentration_risk: str  # low/medium/high
    educational_disclaimer: str


def suggest_sip(
    monthly_income_paise: int,
    mandatory_monthly_dues_paise: int,
    essential_monthly_expenses_paise: int,
) -> int:
    """Calculate suggested SIP amount. All amounts in integer paise."""
    monthly_surplus = monthly_income_paise - mandatory_monthly_dues_paise - essential_monthly_expenses_paise
    if monthly_surplus <= 0:
        return 0
    suggested = min(int(monthly_surplus * 0.20), int(monthly_surplus * 0.50))
    return max(0, suggested)


def assess_concentration(portfolio: List[PortfolioAsset]) -> str:
    """Assess concentration risk from mock portfolio weights.

    Returns 'high' if any single asset > 50% or equity > 70%,
    'medium' if any single asset > 30% or equity > 50%,
    otherwise 'low'.
    """
    if not portfolio:
        return "low"

    max_weight = max(a.weight_percent for a in portfolio)
    equity_weight = sum(a.weight_percent for a in portfolio if a.asset_type == "equity")

    if max_weight > 50 or equity_weight > 70:
        return "high"
    if max_weight > 30 or equity_weight > 50:
        return "medium"
    return "low"


def build_investment_summary(
    monthly_income_paise: int,
    mandatory_monthly_dues_paise: int,
    essential_monthly_expenses_paise: int,
    portfolio_assets: List[PortfolioAsset],
) -> InvestmentSummary:
    """Build the complete educational investment summary."""
    surplus = monthly_income_paise - mandatory_monthly_dues_paise - essential_monthly_expenses_paise
    surplus = max(0, surplus)
    suggested_sip = suggest_sip(
        monthly_income_paise,
        mandatory_monthly_dues_paise,
        essential_monthly_expenses_paise,
    )

    total_value = sum(a.value_paise for a in portfolio_assets)
    # Normalise weights if they don't sum to 100
    assets = list(portfolio_assets)
    if total_value > 0:
        for a in assets:
            a.weight_percent = round(a.value_paise * 100 / total_value)

    concentration_risk = assess_concentration(assets)

    return InvestmentSummary(
        currency="INR",
        monthly_surplus_paise=surplus,
        suggested_sip_paise=suggested_sip,
        portfolio=assets,
        concentration_risk=concentration_risk,
        educational_disclaimer=(
            "Illustrative education only. Not an investment recommendation. "
            "SIP suggestions are based on a simple surplus heuristic and do not "
            "account for your full financial situation, goals or risk profile. "
            "Consult a qualified financial advisor before investing."
        ),
    )
