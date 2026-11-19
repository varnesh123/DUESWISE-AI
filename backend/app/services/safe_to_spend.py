"""Safe-to-spend calculation — blueprint §7 Phase 3.

Formula (all amounts in paise):

    safe_to_spend_paise = max(
        0,
        available_balance_paise
        + projected_income_before_horizon_paise
        - upcoming_mandatory_dues_paise
        - safety_reserve_paise
    )

Default forecast horizon: next 30 days.
Never counts unconfirmed expected income. Prevents duplicate reservation of the
same due.
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.due import Due
from app.models.transaction import Transaction
from app.repositories.due_repository import DueRepository
from app.repositories.transaction_repository import TransactionRepository


class SafeToSpendResult:
    def __init__(
        self,
        available_balance_paise: int,
        upcoming_mandatory_dues_paise: int,
        safety_reserve_paise: int,
        projected_income_paise: int,
        safe_to_spend_paise: int,
        calculation_date: date,
        forecast_horizon_days: int,
        calculated_until: date,
        data_confidence: str,
        next_due: Optional[dict],
    ):
        self.available_balance_paise = available_balance_paise
        self.upcoming_mandatory_dues_paise = upcoming_mandatory_dues_paise
        self.safety_reserve_paise = safety_reserve_paise
        self.projected_income_paise = projected_income_paise
        self.safe_to_spend_paise = safe_to_spend_paise
        self.calculation_date = calculation_date
        self.forecast_horizon_days = forecast_horizon_days
        self.calculated_until = calculated_until
        self.data_confidence = data_confidence
        self.next_due = next_due

    def to_dict(self) -> dict:
        return {
            "currency": "INR",
            "available_balance_paise": self.available_balance_paise,
            "safe_to_spend_paise": self.safe_to_spend_paise,
            "upcoming_dues_total_paise": self.upcoming_mandatory_dues_paise,
            "safety_reserve_paise": self.safety_reserve_paise,
            "projected_income_paise": self.projected_income_paise,
            "calculated_until": self.calculated_until.isoformat(),
            "calculation_date": self.calculation_date.isoformat(),
            "forecast_horizon_days": self.forecast_horizon_days,
            "data_confidence": self.data_confidence,
            "next_due": self.next_due,
        }


def calculate_safe_to_spend(
    db: Session,
    user_id: str,
    calculation_date: date,
    forecast_horizon_days: int | None = None,
    available_balance_paise: int | None = None,
) -> SafeToSpendResult:
    """Calculate safe-to-spend for a user.

    If available_balance_paise is not provided, uses a demo balance derived
    from the user's latest credit transactions.
    """
    if forecast_horizon_days is None:
        forecast_horizon_days = settings.FORECAST_HORIZON_DAYS

    through_date = calculation_date + timedelta(days=forecast_horizon_days)

    # Available balance: use provided value or derive from latest credits
    if available_balance_paise is None:
        repo = TransactionRepository(db)
        transactions, _ = repo.list(
            user_id=user_id,
            page=1,
            page_size=1000,
            transaction_type="credit",
        )
        if transactions:
            # Latest credit by date
            latest = max(transactions, key=lambda t: t.transaction_date)
            available_balance_paise = latest.amount_paise
        else:
            available_balance_paise = 0

    # Upcoming mandatory dues within horizon
    due_repo = DueRepository(db)
    upcoming_dues = due_repo.get_upcoming_mandatory(
        user_id=user_id,
        from_date=calculation_date,
        through_date=through_date,
    )
    upcoming_mandatory_dues_paise = sum(d.amount_paise for d in upcoming_dues)

    # Safety reserve: configured percentage of balance
    reserve_percent = settings.SAFETY_RESERVE_PERCENT
    safety_reserve_paise = int(available_balance_paise * reserve_percent / 100)

    # Projected income: only confirmed expected income before horizon.
    # Manual credits are treated as confirmed; detected income is not counted.
    projected_income_paise = 0  # No unconfirmed income counted

    # Safe to spend
    safe_to_spend_paise = max(
        0,
        available_balance_paise
        + projected_income_paise
        - upcoming_mandatory_dues_paise
        - safety_reserve_paise,
    )

    # Next due (earliest upcoming mandatory due)
    next_due = None
    if upcoming_dues:
        earliest = min(upcoming_dues, key=lambda d: d.due_date)
        next_due = {
            "id": earliest.id,
            "title": earliest.title,
            "amount_paise": earliest.amount_paise,
            "due_date": earliest.due_date.isoformat(),
        }

    # Data confidence
    if upcoming_dues and available_balance_paise > 0:
        data_confidence = "high"
    elif upcoming_dues:
        data_confidence = "medium"
    else:
        data_confidence = "low"

    return SafeToSpendResult(
        available_balance_paise=available_balance_paise,
        upcoming_mandatory_dues_paise=upcoming_mandatory_dues_paise,
        safety_reserve_paise=safety_reserve_paise,
        projected_income_paise=projected_income_paise,
        safe_to_spend_paise=safe_to_spend_paise,
        calculation_date=calculation_date,
        forecast_horizon_days=forecast_horizon_days,
        calculated_until=through_date,
        data_confidence=data_confidence,
        next_due=next_due,
    )
