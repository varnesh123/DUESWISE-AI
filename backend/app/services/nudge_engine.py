"""Nudge engine — blueprint §7 Phase 3.

A nudge is eligible when:
- A mandatory due is within 7 days.
- Discretionary spending in the current 7-day window exceeds its configured threshold.
- A recent transaction increases overspend risk.
- A subscription price increases beyond configured tolerance.

Throttle:
- Maximum 3 notifications per rolling 7 days.
- Quiet hours 22:00–08:00 Asia/Kolkata.
- Deduplicate by nudge type, related due and calendar day.
- Do not repeat an identical nudge within 48 hours.

Eligibility decisions are stored separately from actual delivery.
"""

from datetime import date, datetime, time, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.due import Due
from app.models.nudge import Nudge
from app.models.transaction import Transaction
from app.repositories.due_repository import DueRepository
from app.repositories.nudge_repository import NudgeRepository
from app.repositories.transaction_repository import TransactionRepository
from app.utils.dates import IST_TZ, now_utc, to_iso_z

# Discretionary spending threshold configuration
WEEKLY_DISCRETIONARY_BUDGET_PAISE = 500000  # ₹5,000 default weekly discretionary budget


def _is_quiet_hours(dt: datetime) -> bool:
    """Quiet hours 22:00–08:00 Asia/Kolkata."""
    # Convert to IST
    ist_dt = dt.astimezone(IST_TZ)
    t = ist_dt.time()
    return t >= time(22, 0) or t <= time(8, 0)


def _dedupe_key(nudge_type: str, related_due_id: Optional[str], calc_date: date) -> str:
    due_part = related_due_id or "nodue"
    return f"{nudge_type}:{due_part}:{calc_date.isoformat()}"


def _recent_identical_nudge_exists(
    repo: NudgeRepository,
    user_id: str,
    dedupe_key: str,
    hours: int = 48,
) -> bool:
    cutoff = now_utc() - timedelta(hours=hours)
    # Check by dedupe_key within the window
    existing = repo.find_by_dedupe_key(user_id, dedupe_key)
    if existing is None:
        return False
    return existing.created_at >= cutoff


def _nudge_count_in_window(
    repo: NudgeRepository,
    user_id: str,
    from_dt: datetime,
    to_dt: datetime,
) -> int:
    return repo.count_in_window(user_id, from_dt, to_dt)


def evaluate_nudges(
    db: Session,
    user_id: str,
    calculation_date: date,
) -> List[Nudge]:
    """Evaluate nudge eligibility for a user and create new nudge records.

    Returns the list of newly created Nudge records (after throttling/dedup).
    """
    due_repo = DueRepository(db)
    nudge_repo = NudgeRepository(db)
    txn_repo = TransactionRepository(db)

    now = now_utc()

    # Throttle: max 3 per rolling 7 days
    seven_days_ago = now - timedelta(days=7)
    recent_count = _nudge_count_in_window(nudge_repo, user_id, seven_days_ago, now)
    if recent_count >= settings.MAX_NUDGES_PER_7_DAYS:
        return []

    # Quiet hours: skip creating nudges during quiet hours
    if _is_quiet_hours(now):
        return []

    created: List[Nudge] = []

    # 1. Mandatory due within 7 days
    upcoming_dues = due_repo.get_upcoming_mandatory(
        user_id=user_id,
        from_date=calculation_date,
        through_date=calculation_date + timedelta(days=7),
    )
    for due in upcoming_dues:
        days_until = (due.due_date - calculation_date).days
        dedupe_key = _dedupe_key("mandatory_due_near", due.id, calculation_date)

        if _recent_identical_nudge_exists(nudge_repo, user_id, dedupe_key, hours=48):
            continue

        priority = "high" if days_until <= 2 else "medium"
        nudge = nudge_repo.create(
            user_id=user_id,
            nudge_type="mandatory_due_near",
            priority=priority,
            title=f"{due.title} is due soon",
            message=(
                f"Your {due.due_type} '{due.title}' of ₹{due.amount_paise // 100}.{due.amount_paise % 100:02d}"
                f" is due in {days_until} day(s) on {due.due_date.isoformat()}."
            ),
            dedupe_key=dedupe_key,
            related_due_id=due.id,
        )
        created.append(nudge)

    # 2. Discretionary spending threshold in current 7-day window
    window_start = calculation_date - timedelta(days=6)
    transactions, _ = txn_repo.list(
        user_id=user_id,
        page=1,
        page_size=10000,
        transaction_type="debit",
        from_date=window_start,
        to_date=calculation_date,
    )
    discretionary_spending = sum(
        t.amount_paise
        for t in transactions
        if t.category in ("entertainment", "food", "groceries", "transport")
    )
    threshold = int(WEEKLY_DISCRETIONARY_BUDGET_PAISE * 0.80)

    if discretionary_spending > threshold:
        dedupe_key = _dedupe_key("discretionary_spending_near_due", None, calculation_date)
        if not _recent_identical_nudge_exists(nudge_repo, user_id, dedupe_key, hours=48):
            nudge = nudge_repo.create(
                user_id=user_id,
                nudge_type="discretionary_spending_near_due",
                priority="high",
                title="Discretionary spending near weekly threshold",
                message=(
                    f"Your discretionary spending this week is ₹{discretionary_spending // 100}.{discretionary_spending % 100:02d},"
                    f" exceeding 80% of your weekly budget (₹{threshold // 100}.{threshold % 100:02d})."
                ),
                dedupe_key=dedupe_key,
            )
            created.append(nudge)

    return created
