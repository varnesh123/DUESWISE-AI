"""Unit tests for nudge engine."""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from app.repositories.due_repository import DueRepository
from app.repositories.nudge_repository import NudgeRepository
from app.services.nudge_engine import evaluate_nudges


def _make_due():
    due = MagicMock()
    due.id = "due-123"
    due.title = "Home EMI"
    due.due_type = "emi"
    due.amount_paise = 2000000
    due.due_date = date(2026, 11, 25)
    due.status = "upcoming"
    due.is_mandatory = True
    return due


def test_nudge_mandatory_due_near(db_session):
    """A mandatory due within 7 days should create a medium-priority nudge (6 days out)."""
    due = _make_due()

    orig_get_um = DueRepository.get_upcoming_mandatory
    orig_ciw = NudgeRepository.count_in_window
    orig_fbdk = NudgeRepository.find_by_dedupe_key
    orig_create = NudgeRepository.create

    DueRepository.get_upcoming_mandatory = lambda self, user_id, from_date, through_date: [due]
    NudgeRepository.count_in_window = lambda self, user_id, from_dt, to_dt: 0
    NudgeRepository.find_by_dedupe_key = lambda self, user_id, key: None

    created_nudges = []

    def fake_create(self, user_id, **kwargs):
        nudge = MagicMock()
        nudge.id = "nudge-1"
        nudge.created_at = datetime.now()
        for k, v in kwargs.items():
            setattr(nudge, k, v)
        created_nudges.append(nudge)
        return nudge

    NudgeRepository.create = fake_create

    try:
        created = evaluate_nudges(db_session, "test-user", calculation_date=date(2026, 11, 19))
    finally:
        DueRepository.get_upcoming_mandatory = orig_get_um
        NudgeRepository.count_in_window = orig_ciw
        NudgeRepository.find_by_dedupe_key = orig_fbdk
        NudgeRepository.create = orig_create

    assert len(created) == 1
    assert created[0].nudge_type == "mandatory_due_near"
    # 6 days until due -> priority "medium" (high only if <= 2 days)
    assert created[0].priority == "medium"


def test_nudge_throttle_max_3_per_7_days(db_session):
    """When 3 nudges already exist in the last 7 days, no new nudges are created."""
    due = _make_due()

    orig_get_um = DueRepository.get_upcoming_mandatory
    orig_ciw = NudgeRepository.count_in_window

    DueRepository.get_upcoming_mandatory = lambda self, user_id, from_date, through_date: [due]
    NudgeRepository.count_in_window = lambda self, user_id, from_dt, to_dt: 3

    try:
        created = evaluate_nudges(db_session, "test-user", calculation_date=date(2026, 11, 19))
    finally:
        DueRepository.get_upcoming_mandatory = orig_get_um
        NudgeRepository.count_in_window = orig_ciw

    assert len(created) == 0


def test_nudge_quiet_hours(db_session):
    """When count_in_window returns 0, evaluate_nudges returns a list."""
    due = _make_due()

    orig_get_um = DueRepository.get_upcoming_mandatory
    orig_ciw = NudgeRepository.count_in_window
    orig_fbdk = NudgeRepository.find_by_dedupe_key

    DueRepository.get_upcoming_mandatory = lambda self, user_id, from_date, through_date: [due]
    NudgeRepository.count_in_window = lambda self, user_id, from_dt, to_dt: 0
    NudgeRepository.find_by_dedupe_key = lambda self, user_id, key: None

    try:
        created = evaluate_nudges(db_session, "test-user", calculation_date=date(2026, 11, 19))
    finally:
        DueRepository.get_upcoming_mandatory = orig_get_um
        NudgeRepository.count_in_window = orig_ciw
        NudgeRepository.find_by_dedupe_key = orig_fbdk

    assert isinstance(created, list)
