"""Investment education API routes — CONTRACT.md §13.

Educational only. No real trades or purchases may be executed.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import DbSession, get_current_user
from app.models.user import User
from app.schemas.investment import (
    InvestmentSummaryResponse,
    PortfolioAssetItem,
)
from app.services.investment_guide import (
    InvestmentSummary,
    PortfolioAsset,
    build_investment_summary,
)

router = APIRouter()


def _asset_to_item(asset: PortfolioAsset) -> PortfolioAssetItem:
    return PortfolioAssetItem(
        asset_name=asset.asset_name,
        asset_type=asset.asset_type,
        value_paise=asset.value_paise,
        weight_percent=asset.weight_percent,
    )


@router.get(
    "/investments/summary",
    response_model=InvestmentSummaryResponse,
    tags=["investments"],
    summary="Get educational investment summary",
)
def get_investment_summary(
    db: DbSession,
    current_user: User = Depends(get_current_user),
    monthly_income_paise: int = 0,
    mandatory_monthly_dues_paise: int = 0,
    essential_monthly_expenses_paise: int = 0,
):
    """Generate an educational SIP suggestion and portfolio concentration summary.

    All inputs are query parameters for the MVP. This is an illustrative estimate,
    not investment advice.
    """
    # Default mock portfolio if none provided
    portfolio = [
        PortfolioAsset(
            asset_name="Index Fund",
            asset_type="equity",
            value_paise=5000000,
            weight_percent=75,
        ),
        PortfolioAsset(
            asset_name="Fixed Deposit",
            asset_type="debt",
            value_paise=1666667,
            weight_percent=25,
        ),
    ]

    summary = build_investment_summary(
        monthly_income_paise=monthly_income_paise,
        mandatory_monthly_dues_paise=mandatory_monthly_dues_paise,
        essential_monthly_expenses_paise=essential_monthly_expenses_paise,
        portfolio_assets=portfolio,
    )

    return InvestmentSummaryResponse(
        currency=summary.currency,
        monthly_surplus_paise=summary.monthly_surplus_paise,
        suggested_sip_paise=summary.suggested_sip_paise,
        portfolio=[_asset_to_item(a) for a in summary.portfolio],
        concentration_risk=summary.concentration_risk,
        educational_disclaimer=summary.educational_disclaimer,
    )
