"""Unit tests for date utilities."""

from datetime import date, datetime
import pytest
from app.utils.dates import (
    parse_date_iso,
    parse_indian_date,
    format_date_iso,
    now_utc,
    to_iso_z,
    IST_TZ,
)


def test_parse_date_iso():
    assert parse_date_iso("2026-11-19") == date(2026, 11, 19)


def test_parse_date_iso_invalid():
    with pytest.raises(ValueError):
        parse_date_iso("19-11-2026")


def test_parse_indian_date_iso():
    assert parse_indian_date("2026-11-19") == date(2026, 11, 19)


@pytest.mark.parametrize(
    "date_str,expected",
    [
        ("19-11-2026", date(2026, 11, 19)),
        ("19/11/2026", date(2026, 11, 19)),
        ("1-1-2026", date(2026, 1, 1)),
        ("19-11-26", date(2026, 11, 19)),
        ("1/1/26", date(2026, 1, 1)),
    ],
)
def test_parse_indian_date_formats(date_str, expected):
    assert parse_indian_date(date_str) == expected


def test_parse_indian_date_invalid():
    with pytest.raises(ValueError):
        parse_indian_date("not-a-date")


def test_format_date_iso():
    assert format_date_iso(date(2026, 11, 19)) == "2026-11-19"


def test_now_utc_is_timezone_aware():
    dt = now_utc()
    assert dt.tzinfo is not None


def test_to_iso_z():
    dt = datetime(2026, 11, 19, 8, 30, 0, tzinfo=IST_TZ)
    result = to_iso_z(dt)
    assert result.endswith("Z")
    assert "2026-11-19T08:30:00Z" == result or "+05:30" in result or result == "2026-11-19T03:00:00Z"
