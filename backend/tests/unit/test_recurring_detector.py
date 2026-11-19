"""Unit tests for recurring payment detection."""

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.recurring_detector import detect_recurring_transactions


def _make_txn(merchant, category, amount_paise, txn_date, payment_method="upi"):
    txn = MagicMock()
    txn.merchant_normalized = merchant
    txn.category = category
    txn.amount_paise = amount_paise
    txn.transaction_date = txn_date
    txn.payment_method = payment_method
    txn.transaction_type = "debit"
    return txn


def test_detect_monthly_recurring(db_session):
    """Three monthly Netflix transactions should create an uncertain subscription."""
    base = date(2026, 9, 18)
    txns = [
        _make_txn("NETFLIX", "entertainment", 49900, base - timedelta(days=60)),
        _make_txn("NETFLIX", "entertainment", 49900, base - timedelta(days=30)),
        _make_txn("NETFLIX", "entertainment", 49900, base),
    ]

    # Mock repository list to return our transactions
    from app.repositories.transaction_repository import TransactionRepository
    from app.repositories.subscription_repository import SubscriptionRepository

    orig_list = TransactionRepository.list
    TransactionRepository.list = lambda self, user_id, **kw: (txns, len(txns))
    orig_sub_list = SubscriptionRepository.list
    SubscriptionRepository.list = lambda self, user_id: ([], 0)

    try:
        created = detect_recurring_transactions(db_session, "test-user")
    finally:
        TransactionRepository.list = orig_list
        SubscriptionRepository.list = orig_sub_list

    assert len(created) == 1
    sub = created[0]
    assert sub.merchant == "NETFLIX"
    assert sub.category == "entertainment"
    assert sub.frequency == "monthly"
    assert sub.status == "uncertain"
    assert sub.is_user_confirmed is False
    assert sub.expected_amount_paise == 49900
    assert sub.detection_confidence > 0


def test_detect_insufficient_occurrences(db_session):
    """Two transactions should not create a subscription (need >= 3)."""
    base = date(2026, 9, 18)
    txns = [
        _make_txn("NETFLIX", "entertainment", 49900, base - timedelta(days=30)),
        _make_txn("NETFLIX", "entertainment", 49900, base),
    ]

    from app.repositories.transaction_repository import TransactionRepository
    from app.repositories.subscription_repository import SubscriptionRepository

    orig_list = TransactionRepository.list
    TransactionRepository.list = lambda self, user_id, **kw: (txns, len(txns))
    orig_sub_list = SubscriptionRepository.list
    SubscriptionRepository.list = lambda self, user_id: ([], 0)

    try:
        created = detect_recurring_transactions(db_session, "test-user")
    finally:
        TransactionRepository.list = orig_list
        SubscriptionRepository.list = orig_sub_list

    assert len(created) == 0


def test_detect_interval_outside_tolerance(db_session):
    """Transactions with 10-day intervals (weekly-ish but outside 5-10? Actually weekly is 5-10).
    Let's test 50-day intervals which don't match any tolerance."""
    base = date(2026, 9, 18)
    txns = [
        _make_txn("RANDOM", "other", 10000, base - timedelta(days=100)),
        _make_txn("RANDOM", "other", 10000, base - timedelta(days=50)),
        _make_txn("RANDOM", "other", 10000, base),
    ]

    from app.repositories.transaction_repository import TransactionRepository
    from app.repositories.subscription_repository import SubscriptionRepository

    orig_list = TransactionRepository.list
    TransactionRepository.list = lambda self, user_id, **kw: (txns, len(txns))
    orig_sub_list = SubscriptionRepository.list
    SubscriptionRepository.list = lambda self, user_id: ([], 0)

    try:
        created = detect_recurring_transactions(db_session, "test-user")
    finally:
        TransactionRepository.list = orig_list
        SubscriptionRepository.list = orig_sub_list

    # 50-day interval doesn't match monthly (25-35) or quarterly (80-100)
    assert len(created) == 0


def test_detect_amount_deviation(db_session):
    """Large amount deviation (>15%) should reduce confidence but still detect if interval matches."""
    base = date(2026, 9, 18)
    txns = [
        _make_txn("NETFLIX", "entertainment", 49900, base - timedelta(days=60)),
        _make_txn("NETFLIX", "entertainment", 49900, base - timedelta(days=30)),
        _make_txn("NETFLIX", "entertainment", 99900, base),  # 100% deviation
    ]

    from app.repositories.transaction_repository import TransactionRepository
    from app.repositories.subscription_repository import SubscriptionRepository

    orig_list = TransactionRepository.list
    TransactionRepository.list = lambda self, user_id, **kw: (txns, len(txns))
    orig_sub_list = SubscriptionRepository.list
    SubscriptionRepository.list = lambda self, user_id: ([], 0)

    try:
        created = detect_recurring_transactions(db_session, "test-user")
    finally:
        TransactionRepository.list = orig_list
        SubscriptionRepository.list = orig_sub_list

    assert len(created) == 1
    # Amount inconsistent => lower confidence
    assert created[0].detection_confidence < 1.0
