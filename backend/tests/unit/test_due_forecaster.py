"""Unit tests for due forecasting."""

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.due_forecaster import forecast_next_due, infer_dues_from_transactions


def _make_due(due_type, amount_paise, due_date, source="manual", is_mandatory=True):
    due = MagicMock()
    due.due_type = due_type
    due.amount_paise = amount_paise
    due.due_date = due_date
    due.source = source
    due.is_mandatory = is_mandatory
    return due


def test_forecast_next_due_manual_history(db_session):
    """Two manual EMI dues should forecast the next one using median interval."""
    d1 = date(2026, 9, 25)
    d2 = date(2026, 10, 25)
    dues = [
        _make_due("emi", 2000000, d1),
        _make_due("emi", 2000000, d2),
    ]

    from app.repositories.due_repository import DueRepository
    orig_list = DueRepository.list
    DueRepository.list = lambda self, user_id: (dues, len(dues))

    try:
        result = forecast_next_due(db_session, "test-user", "emi", 2000000, date(2026, 11, 1))
    finally:
        DueRepository.list = orig_list

    assert result is not None
    # 30-day median interval, last due Oct 25 -> Nov 24
    assert result == date(2026, 11, 24)


def test_forecast_insufficient_history(db_session):
    """One manual due should return None (need >= 2)."""
    dues = [_make_due("emi", 2000000, date(2026, 10, 25))]

    from app.repositories.due_repository import DueRepository
    orig_list = DueRepository.list
    DueRepository.list = lambda self, user_id: (dues, len(dues))

    try:
        result = forecast_next_due(db_session, "test-user", "emi", 2000000, date(2026, 11, 1))
    finally:
        DueRepository.list = orig_list

    assert result is None


def test_forecast_different_type_ignored(db_session):
    """EMI dues should not be mixed with rent dues."""
    dues = [
        _make_due("emi", 2000000, date(2026, 9, 25)),
        _make_due("emi", 2000000, date(2026, 10, 25)),
        _make_due("rent", 1500000, date(2026, 10, 5)),
    ]

    from app.repositories.due_repository import DueRepository
    orig_list = DueRepository.list
    DueRepository.list = lambda self, user_id: (dues, len(dues))

    try:
        # Request rent forecast - only 1 rent due, so None
        result = forecast_next_due(db_session, "test-user", "rent", 1500000, date(2026, 11, 1))
    finally:
        DueRepository.list = orig_list

    assert result is None
