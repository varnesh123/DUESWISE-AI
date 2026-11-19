"""Dashboard summary route — safe-to-spend dashboard (CONTRACT.md §4).

Returns the safe-to-spend calculation with all components disclosed.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import DbSession, get_current_user
from app.models.user import User
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.common import ErrorDetail, ErrorResponse
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    NextDueItem,
)
from app.services.safe_to_spend import calculate_safe_to_spend
from app.utils.dates import parse_date_iso, now_utc, IST_TZ

router = APIRouter()


@router.get(
    "/dashboard/summary",
    response_model=DashboardSummaryResponse,
    tags=["dashboard"],
    summary="Get dashboard summary with safe-to-spend",
)
def dashboard_summary(
    db: DbSession,
    current_user: User = Depends(get_current_user),
    calculation_date: str | None = None,
    available_balance_paise: int | None = None,
):
    """Return the safe-to-spend dashboard summary for the current user.

    The calculation date defaults to today (Asia/Kolkata). All amounts are in
    paise. The dashboard discloses calculation date, horizon and components.
    """
    if calculation_date is None:
        calc_date = now_utc().astimezone(IST_TZ).date()
    else:
        try:
            calc_date = parse_date_iso(calculation_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="calculation_date must be YYYY-MM-DD",
            )

    result = calculate_safe_to_spend(
        db=db,
        user_id=current_user.id,
        calculation_date=calc_date,
        available_balance_paise=available_balance_paise,
    )

    # Recent transactions (up to 5)
    txn_repo = TransactionRepository(db)
    recent, _ = txn_repo.list(user_id=current_user.id, page=1, page_size=5)
    recent_transactions = [
        {
            "id": t.id,
            "amount_paise": t.amount_paise,
            "transaction_type": t.transaction_type,
            "merchant_normalized": t.merchant_normalized,
            "category": t.category,
            "transaction_date": t.transaction_date.isoformat(),
        }
        for t in recent
    ]

    return DashboardSummaryResponse(
        currency=result.to_dict()["currency"],
        available_balance_paise=result.available_balance_paise,
        safe_to_spend_paise=result.safe_to_spend_paise,
        upcoming_dues_total_paise=result.upcoming_mandatory_dues_paise,
        safety_reserve_paise=result.safety_reserve_paise,
        projected_income_paise=result.projected_income_paise,
        calculated_until=result.calculated_until.isoformat(),
        calculation_date=result.calculation_date.isoformat(),
        forecast_horizon_days=result.forecast_horizon_days,
        data_confidence=result.data_confidence,
        next_due=(
            NextDueItem(
                id=result.next_due["id"],
                title=result.next_due["title"],
                amount_paise=result.next_due["amount_paise"],
                due_date=result.next_due["due_date"],
            )
            if result.next_due
            else None
        ),
        recent_transactions=recent_transactions,
    )
