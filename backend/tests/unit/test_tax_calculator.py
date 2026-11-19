"""Unit tests for tax calculator."""

import pytest

from app.services.tax_calculator import compare_tax_regimes, _calculate_regime, _slab_tax


def test_slab_tax_basic():
    """Tax on ₹12 lakh under old regime slabs."""
    slabs = [
        {"min_paise": 0, "max_paise": 25000000, "rate_basis_points": 0},
        {"min_paise": 25000000, "max_paise": 50000000, "rate_basis_points": 500},
        {"min_paise": 50000000, "max_paise": 100000000, "rate_basis_points": 2000},
        {"min_paise": 100000000, "max_paise": None, "rate_basis_points": 3000},
    ]
    # ₹1,20,00,000 taxable: 0 on first 2.5L + 5% on next 2.5L + 20% on next 5L + 30% on remaining 2L
    # = 0 + 1250000 + 10000000 + 6000000 = 17250000
    tax = _slab_tax(120000000, slabs)
    assert tax == 17250000


def test_compare_tax_regimes_basic():
    """Compare tax for ₹12 lakh salary with ₹20 lakh deductions."""
    result = compare_tax_regimes(
        financial_year="FY-2025-26",
        annual_salary_paise=12000000,
        deductions={
            "section_80c_paise": 1500000,
            "section_80d_paise": 250000,
            "section_80ccd_1b_paise": 500000,
            "hra_exemption_paise": 0,
            "home_loan_interest_paise": 0,
            "other_eligible_deductions_paise": 0,
        },
    )
    assert result.financial_year == "FY-2025-26"
    assert result.gross_salary_paise == 12000000
    assert result.lower_tax_regime in ("old", "new")
    assert result.estimated_savings_paise >= 0
    assert "not professional tax advice" in result.disclaimer
    assert result.rules_metadata["verification_status"] == "unverified"


def test_compare_tax_regimes_unsupported_year():
    """Unsupported financial year should raise ValueError."""
    with pytest.raises(ValueError, match="not available"):
        compare_tax_regimes(
            financial_year="FY-2024-25",
            annual_salary_paise=1200000,
            deductions={},
        )


def test_old_regime_standard_deduction():
    """Old regime standard deduction of ₹50,000."""
    rules_result = _calculate_regime(
        6000000, {}, "old",
        {"regimes": {"old": {
            "standard_deduction_paise": 5000000,
            "rebate_limit_paise": 0,
            "rebate_max_income_paise": 0,
            "cess_rate_basis_points": 0,
            "surcharge_thresholds": [],
            "deductions": {"section_80c_paise": 0, "section_80d_paise": 0, "section_80ccd_1b_paise": 0, "hra_exemption_paise": 0, "home_loan_interest_paise": 0, "other_eligible_deductions_paise": 0},
            "slabs": [{"min_paise": 0, "max_paise": None, "rate_basis_points": 0}],
        }, "new": {}},
        "rules_metadata": {},
    })
    assert rules_result.standard_deduction_paise == 5000000
    assert rules_result.taxable_income_paise == 1000000
