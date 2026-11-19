"""Recurring payment detection — blueprint §7 Phase 3.

Groups transactions by (user_id, merchant_normalized, category, transaction_type)
and identifies recurring candidates with at least three occurrences. Uses median
interval and median amount. Amount variation tolerance: relative deviation <= 15%.

Creates detected subscription records as `uncertain` until user confirmation.
"""

import statistics
from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.transaction_repository import TransactionRepository

# Tolerance windows in days for interval classification
INTERVAL_TOLERANCE = {
    "weekly": (5, 10),
    "monthly": (25, 35),
    "quarterly": (80, 100),
    "yearly": (350, 380),
}

AMOUNT_DEVIATION_TOLERANCE = 0.15  # 15%
MIN_OCCURRENCES = 3


def _median(values: List[float]) -> float:
    return statistics.median(values) if values else 0.0


def _classify_interval(avg_days: float) -> Optional[str]:
    """Classify an average interval in days into a frequency bucket."""
    for freq, (lo, hi) in INTERVAL_TOLERANCE.items():
        if lo <= avg_days <= hi:
            return freq
    return None


def _relative_deviation(amount: int, median_amount: float) -> float:
    if median_amount == 0:
        return 1.0
    return abs(amount - median_amount) / median_amount


def _compute_confidence(
    occurrences: int,
    interval_consistent: bool,
    amount_consistent: bool,
) -> float:
    """Confidence based on observations, interval consistency, amount consistency."""
    score = 0.0
    # Observations component (max 0.4)
    score += min(occurrences / 12.0, 1.0) * 0.4
    # Interval consistency (max 0.3)
    if interval_consistent:
        score += 0.3
    # Amount consistency (max 0.3)
    if amount_consistent:
        score += 0.3
    return round(score, 2)


def detect_recurring_transactions(db: Session, user_id: str) -> List[Subscription]:
    """Scan the user's transactions and create `uncertain` subscription records
    for detected recurring patterns.

    Returns the list of newly created Subscription records.
    """
    repo = TransactionRepository(db)
    sub_repo = SubscriptionRepository(db)

    # Fetch all debit transactions for the user, ordered by date
    transactions, _ = repo.list(
        user_id=user_id,
        page=1,
        page_size=10000,
        transaction_type="debit",
    )

    # Group by (merchant_normalized, category)
    groups: dict[tuple[str, str], List[Transaction]] = {}
    for txn in transactions:
        key = (txn.merchant_normalized, txn.category)
        groups.setdefault(key, []).append(txn)

    created: List[Subscription] = []

    for (merchant, category), txns in groups.items():
        if len(txns) < MIN_OCCURRENCES:
            continue

        # Sort by transaction date
        txns.sort(key=lambda t: t.transaction_date)

        # Compute intervals between consecutive transactions
        intervals: List[int] = []
        for i in range(1, len(txns)):
            delta = (txns[i].transaction_date - txns[i - 1].transaction_date).days
            if delta > 0:
                intervals.append(delta)

        if not intervals:
            continue

        median_interval = _median(intervals)
        frequency = _classify_interval(median_interval)
        if frequency is None:
            continue  # interval doesn't match any supported frequency

        # Interval consistency: median within tolerance band
        lo, hi = INTERVAL_TOLERANCE[frequency]
        interval_consistent = lo <= median_interval <= hi

        # Amount consistency
        amounts = [t.amount_paise for t in txns]
        median_amount = _median(amounts)
        amount_deviations = [
            _relative_deviation(a, median_amount) for a in amounts
        ]
        amount_consistent = all(d <= AMOUNT_DEVIATION_TOLERANCE for d in amount_deviations)

        confidence = _compute_confidence(len(txns), interval_consistent, amount_consistent)

        # Next due date = last transaction date + median interval
        last_date = txns[-1].transaction_date
        next_due = last_date + timedelta(days=int(round(median_interval)))

        # Check if an uncertain subscription already exists for this merchant
        existing_subs, _ = sub_repo.list(user_id=user_id)
        already_exists = any(
            s.merchant.lower() == merchant.lower()
            and s.category.lower() == category.lower()
            and s.status == "uncertain"
            for s in existing_subs
        )
        if already_exists:
            continue

        sub = sub_repo.create(
            user_id=user_id,
            merchant=merchant,
            category=category,
            expected_amount_paise=int(median_amount),
            frequency=frequency,
            next_due_date=next_due,
            detection_confidence=confidence,
            status="uncertain",
            is_user_confirmed=False,
        )
        created.append(sub)

    return created
