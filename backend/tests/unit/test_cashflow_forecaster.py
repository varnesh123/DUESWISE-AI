"""Unit tests for cash flow forecaster."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.services.cashflow_forecaster import calculate_cash_flow


def test_cash_flow_basic(db_session):
    """Cash flow calculation with sales, expenses, receivables, payables."""
    from app.repositories.business_repository import BusinessRepository

    entries = [
        MagicMock(entry_type="sale", amount_paise=12000000, status="paid"),
        MagicMock(entry_type="expense", amount_paise=4000000, status="paid"),
        MagicMock(entry_type="receivable", amount_paise=3000000, status="pending"),
        MagicMock(entry_type="receivable", amount_paise=500000, status="paid"),
        MagicMock(entry_type="payable", amount_paise=2500000, status="pending"),
        MagicMock(entry_type="payable", amount_paise=1000000, status="paid"),
    ]
    BusinessRepository.list = lambda self, user_id: (entries, len(entries))

    try:
        result = calculate_cash_flow(
            db_session,
            "test-user",
            current_cash_paise=5000000,
            forecast_date="2026-12-19",
        )
    finally:
        pass

    assert result.current_cash_paise == 5000000
    assert result.total_sales_paise == 12000000
    assert result.total_expenses_paise == 4000000
    assert result.pending_receivables_paise == 3000000  # only pending
    assert result.pending_payables_paise == 2500000  # only pending
    # projected = 5000000 + 3000000 - 2500000 + (12000000 - 4000000)
    expected = 5000000 + 3000000 - 2500000 + 8000000
    assert result.projected_cash_balance_paise == expected
    assert result.forecast_date == "2026-12-19"


def test_cash_flow_no_double_counting(db_session):
    """Paid receivables are not counted as pending."""
    from app.repositories.business_repository import BusinessRepository

    entries = [
        MagicMock(entry_type="receivable", amount_paise=3000000, status="paid"),
    ]
    BusinessRepository.list = lambda self, user_id: (entries, len(entries))

    try:
        result = calculate_cash_flow(
            db_session,
            "test-user",
            current_cash_paise=5000000,
            forecast_date="2026-12-19",
        )
    finally:
        pass

    assert result.pending_receivables_paise == 0
    assert result.projected_cash_balance_paise == 5000000
