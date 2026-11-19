"""Due forecasting — blueprint §7 Phase 3.

Calculates next expected due date using median historical interval.
Uses explicit manually entered dues as higher-confidence records than inferred dues.
Allows user correction (via the dues API).
"""

from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

import statistics

from app.models.due import Due
from app.models.transaction import Transaction
from app.repositories.due_repository import DueRepository
from app.repositories.transaction_repository import TransactionRepository


def _median(values: List[float]) -> float:
    return statistics.median(values) if values else 0.0


def forecast_next_due(
    db: Session,
    user_id: str,
    due_type: str,
    amount_paise: int,
    reference_date: date,
) -> Optional[date]:
    """Forecast the next due date for a given due_type based on historical
    manual dues of the same type.

    Uses the median interval between existing manual dues. Returns None if
    there is insufficient history.
    """
    repo = DueRepository(db)
    dues, _ = repo.list(user_id=user_id)

    # Filter to manual dues of the same type that are before reference_date
    relevant = [
        d for d in dues
        if d.due_type == due_type
        and d.source == "manual"
        and d.due_date < reference_date
    ]

    if len(relevant) < 2:
        return None

    relevant.sort(key=lambda d: d.due_date)
    intervals: List[int] = []
    for i in range(1, len(relevant)):
        delta = (relevant[i].due_date - relevant[i - 1].due_date).days
        if delta > 0:
            intervals.append(delta)

    if not intervals:
        return None

    median_interval = _median(intervals)
    last_due = relevant[-1].due_date
    return last_due + timedelta(days=int(round(median_interval)))


def infer_dues_from_transactions(
    db: Session,
    user_id: str,
) -> List[Due]:
    """Infer due records from detected subscriptions.

    Detected subscriptions (status uncertain) are converted into inferred due
    records with lower confidence than manual dues.
    """
    from app.repositories.subscription_repository import SubscriptionRepository

    sub_repo = SubscriptionRepository(db)
    due_repo = DueRepository(db)

    subs, _ = sub_repo.list(user_id=user_id)
    inferred: List[Due] = []

    for sub in subs:
        if sub.status != "uncertain":
            continue

        # Avoid duplicating an existing manual due for the same merchant/date
        existing_dues, _ = due_repo.list(user_id=user_id)
        already_exists = any(
            d.title.lower() == sub.merchant.lower()
            and abs((d.due_date - sub.next_due_date).days) <= 2
            for d in existing_dues
        )
        if already_exists:
            continue

        due = due_repo.create(
            user_id=user_id,
            title=f"Recurring: {sub.merchant}",
            due_type="subscription",
            amount_paise=sub.expected_amount_paise,
            due_date=sub.next_due_date,
            frequency=sub.frequency,
            status="upcoming",
            is_mandatory=False,
            confidence=sub.detection_confidence,
            source="detected",
        )
        inferred.append(due)

    return inferred
