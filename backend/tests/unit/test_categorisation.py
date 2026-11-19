"""Unit tests for deterministic merchant categorisation."""

import pytest
from app.services.categorisation import categorise_merchant, categorise_keywords


def test_alias_match_netflix():
    norm, cat, conf = categorise_merchant("NETFLIX INDIA PVT LTD")
    assert norm == "Netflix"
    assert cat == "entertainment"
    assert conf >= 0.9


def test_alias_match_swiggy():
    norm, cat, conf = categorise_merchant("SWIGGY INSTAMART ORDER")
    assert norm == "Swiggy"
    assert cat == "food"


def test_airtel_utilities():
    norm, cat, conf = categorise_merchant("AIRTEL MOBILE BILL")
    assert cat == "utilities"


def test_salary_credit():
    norm, cat, conf = categorise_merchant("SALARY CREDIT NOVEMBER")
    assert cat == "salary"


def test_unknown_merchant_falls_back_to_other():
    norm, cat, conf = categorise_merchant("XYZ RANDOM SHOP")
    assert cat == "other"
    assert conf == 0.3


def test_keyword_match_fallback():
    norm, cat, conf = categorise_merchant("SOME LOCAL GROCERY STORE")
    assert cat == "groceries"


def test_categorise_keywords():
    assert categorise_keywords(["netflix", "subscription"]) == "entertainment"
    assert categorise_keywords(["salary", "credit"]) == "salary"
    assert categorise_keywords(["unknown", "thing"]) == "other"


def test_ai_suggestion_only_when_unresolved():
    # Deterministic resolves to entertainment, AI suggestion should be ignored.
    norm, cat, conf = categorise_merchant(
        "NETFLIX INDIA",
        ai_normalized="Disney+",
        ai_category="entertainment",
        ai_confidence=0.99,
    )
    assert cat == "entertainment"
    assert norm == "Netflix"

    # Deterministic is "other", AI suggestion is used (capped at 0.75).
    norm, cat, conf = categorise_merchant(
        "XYZ RANDOM SHOP",
        ai_normalized="XYZ Shop",
        ai_category="food",
        ai_confidence=0.99,
    )
    assert cat == "food"
    assert conf <= 0.75
