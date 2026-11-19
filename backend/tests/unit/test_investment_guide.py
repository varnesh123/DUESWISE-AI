"""Unit tests for investment guide."""

import pytest

from app.services.investment_guide import (
    suggest_sip,
    assess_concentration,
    build_investment_summary,
    PortfolioAsset,
)


def test_suggest_sip_positive_surplus():
    """₹1,00,000 surplus -> suggested SIP = min(20%, 50%) = ₹20,000."""
    sip = suggest_sip(10000000, 5000000, 3000000)  # income 10L, dues 5L, expenses 3L
    # surplus = 2L, 20% = 40000, 50% = 100000, min = 40000
    assert sip == 400000


def test_suggest_sip_zero_surplus():
    """Zero or negative surplus -> suggested SIP = 0."""
    assert suggest_sip(5000000, 5000000, 0) == 0
    assert suggest_sip(3000000, 5000000, 0) == 0


def test_assess_concentration_high():
    """Single asset > 50% = high concentration."""
    portfolio = [
        PortfolioAsset("Stock A", "equity", 6000000, 60),
        PortfolioAsset("Bond B", "debt", 4000000, 40),
    ]
    assert assess_concentration(portfolio) == "high"


def test_assess_concentration_medium():
    """Single asset 30-50% OR equity 50-70% = medium concentration."""
    portfolio = [
        PortfolioAsset("Stock A", "equity", 4000000, 40),
        PortfolioAsset("Bond B", "debt", 3000000, 30),
        PortfolioAsset("Cash C", "debt", 3000000, 30),
    ]
    assert assess_concentration(portfolio) == "medium"


def test_assess_concentration_low():
    """Well diversified = low concentration."""
    portfolio = [
        PortfolioAsset("A", "equity", 2500000, 25),
        PortfolioAsset("B", "debt", 2500000, 25),
        PortfolioAsset("C", "hybrid", 2500000, 25),
        PortfolioAsset("D", "gold", 2500000, 25),
    ]
    assert assess_concentration(portfolio) == "low"


def test_build_investment_summary():
    """Complete investment summary with SIP and concentration."""
    portfolio = [
        PortfolioAsset("Index Fund", "equity", 5000000, 75),
        PortfolioAsset("Fixed Deposit", "debt", 1666667, 25),
    ]
    summary = build_investment_summary(
        monthly_income_paise=10000000,
        mandatory_monthly_dues_paise=5000000,
        essential_monthly_expenses_paise=3000000,
        portfolio_assets=portfolio,
    )
    assert summary.monthly_surplus_paise == 2000000
    assert summary.suggested_sip_paise == 400000
    assert summary.concentration_risk == "high"  # equity 75% > 70%
    assert "not an investment recommendation" in summary.educational_disclaimer.lower()
