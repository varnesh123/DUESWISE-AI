"""Unit tests for safe-to-spend calculation."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.services.safe_to_spend import calculate_safe_to_spend


def test_safe_to_spend_basic(db_session):
    """Safe to spend = balance + income - dues - reserve, floored at 0."""
    from app.repositories.transaction_repository import TransactionRepository
    from app.repositories.due_repository import DueRepository

    orig_list = TransactionRepository.list
    orig_get_um = DueRepository.get_upcoming_mandatory

    txns = [MagicMock(amount_paise=1000000, transaction_date=date(2026, 11, 1), transaction_type="credit")]
    TransactionRepository.list = lambda self, user_id, **kw: (txns, len(txns))

    dues = [
        MagicMock(amount_paise=2000000, due_date=date(2026, 11, 25), is_mandatory=True, status="upcoming"),
    ]
    DueRepository.get_upcoming_mandatory = lambda self, user_id, from_date, through_date: dues

    try:
        result = calculate_safe_to_spend(
            db_session,
            "test-user",
            calculation_date=date(2026, 11, 19),
            forecast_horizon_days=30,
            available_balance_paise=5000000,
        )
    finally:
        TransactionRepository.list = orig_list
        DueRepository.get_upcoming_mandatory = orig_get_um

    assert result.available_balance_paise == 5000000
    assert result.upcoming_mandatory_dues_paise == 2000000
    assert result.safety_reserve_paise == int(5000000 * 10 / 100)  # 500000
    assert result.projected_income_paise == 0
    assert result.safe_to_spend_paise == max(0, 5000000 + 0 - 2000000 - 500000)
    assert result.safe_to_spend_paise == 2500000
    assert result.calculation_date == date(2026, 11, 19)
    assert result.forecast_horizon_days == 30
    assert result.next_due is not None
    assert result.next_due["title"] is not None


def test_safe_to_spend_floored_at_zero(db_session):
    """When dues exceed balance + income, safe to spend is 0."""
    from app.repositories.transaction_repository import TransactionRepository
    from app.repositories.due_repository import DueRepository

    orig_list = TransactionRepository.list
    orig_get_um = DueRepository.get_upcoming_mandatory

    TransactionRepository.list = lambda self, user_id, **kw: ([], 0)
    DueRepository.get_upcoming_mandatory = lambda self, user_id, from_date, through_date: [
        MagicMock(amount_paise=10000000, due_date=date(2026, 11, 25), is_mandatory=True, status="upcoming"),
    ]

    try:
        result = calculate_safe_to_spend(
            db_session,
            "test-user",
            calculation_date=date(2026, 11, 19),
            available_balance_paise=1000000,
        )
    finally:
        TransactionRepository.list = orig_list
        DueRepository.get_upcoming_mandatory = orig_get_um

    assert result.safe_to_spend_paise == 0
    assert result.available_balance_paise == 1000000
    assert result.upcoming_mandatory_dues_paise == 10000000


def test_safe_to_spend_no_dues(db_session):
    """No upcoming dues means safe to spend = balance - reserve."""
    from app.repositories.transaction_repository import TransactionRepository
    from app.repositories.due_repository import DueRepository

    orig_list = TransactionRepository.list
    orig_get_um = DueRepository.get_upcoming_mandatory

    TransactionRepository.list = lambda self, user_id, **kw: ([], 0)
    DueRepository.get_upcoming_mandatory = lambda self, user_id, from_date, through_date: []

    try:
        result = calculate_safe_to_spend(
            db_session,
            "test-user",
            calculation_date=date(2026, 11, 19),
            available_balance_paise=5000000,
        )
    finally:
        TransactionRepository.list = orig_list
        DueRepository.get_upcoming_mandatory = orig_get_um

    assert result.upcoming_mandatory_dues_paise == 0
    assert result.safety_reserve_paise == 500000
    assert result.safe_to_spend_paise == 4500000
    assert result.next_due is None
    assert result.data_confidence == "low"
