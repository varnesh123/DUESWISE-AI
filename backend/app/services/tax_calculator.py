"""Income tax regime comparison — blueprint §7 Phase 3.

Deterministic old/new regime tax calculations using configurable rules in
rules/tax_rules.json. All amounts in integer paise.

The initial tax-rule file clearly identifies its financial year and verification
status (unverified — not yet checked against Income Tax Department publications).

Calculates tax using slab-wise marginal rates. Includes standard deduction,
eligible rebate, and cess. Shows tax under both regimes and the difference.

Disclaimer: informational estimate, not professional tax advice.
"""

import json
import os
from dataclasses import dataclass
from typing import Optional

_RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "rules", "tax_rules.json")


@dataclass
class RegimeResult:
    gross_income_paise: int
    standard_deduction_paise: int
    eligible_deductions_paise: int
    taxable_income_paise: int
    income_tax_paise: int
    cess_paise: int
    surcharge_paise: int
    total_tax_paise: int
    rebate_applied_paise: int = 0


@dataclass
class TaxComparisonResult:
    financial_year: str
    gross_salary_paise: int
    old_regime: RegimeResult
    new_regime: RegimeResult
    lower_tax_regime: str
    estimated_savings_paise: int
    disclaimer: str
    rules_metadata: dict


def _load_rules() -> dict:
    with open(_RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _slab_tax(taxable_income_paise: int, slabs: list) -> int:
    """Calculate tax using slab-wise marginal rates. Returns tax in paise."""
    tax = 0
    for slab in slabs:
        min_paise = slab["min_paise"]
        max_paise = slab["max_paise"]
        rate_bp = slab["rate_basis_points"]
        if taxable_income_paise > min_paise:
            upper = max_paise if max_paise is not None else taxable_income_paise
            slab_amount = min(taxable_income_paise, upper) - min_paise
            if slab_amount > 0:
                tax += int(slab_amount * rate_bp / 10000)
    return tax


def _apply_surcharge(tax_paise: int, income_paise: int, thresholds: list) -> int:
    """Apply surcharge based on income thresholds. Returns surcharge in paise."""
    surcharge = 0
    applicable_rate = 0
    for thresh in thresholds:
        if income_paise > thresh["threshold_paise"]:
            applicable_rate = thresh["rate_basis_points"]
    if applicable_rate > 0:
        surcharge = int(tax_paise * applicable_rate / 10000)
    return surcharge


def _calculate_regime(
    gross_income_paise: int,
    deductions: dict,
    regime: str,
    rules: dict,
) -> RegimeResult:
    regime_rules = rules["regimes"][regime]
    slab_list = regime_rules["slabs"]
    std_deduction = regime_rules["standard_deduction_paise"]
    cess_bp = regime_rules["cess_rate_basis_points"]
    surcharge_thresholds = regime_rules.get("surcharge_thresholds", [])
    reg_deductions = regime_rules.get("deductions", {})

    # Standard deduction applies under both regimes
    after_std = max(0, gross_income_paise - std_deduction)

    # Eligible deductions only under the applicable regime
    eligible_deductions = 0
    if regime == "old":
        sec_80c = min(deductions.get("section_80c_paise", 0), reg_deductions.get("section_80c_paise", 0))
        sec_80d = min(deductions.get("section_80d_paise", 0), reg_deductions.get("section_80d_paise", 0))
        sec_80ccd = min(deductions.get("section_80ccd_1b_paise", 0), reg_deductions.get("section_80ccd_1b_paise", 0))
        hra = deductions.get("hra_exemption_paise", 0) or 0
        home_loan = min(deductions.get("home_loan_interest_paise", 0), reg_deductions.get("home_loan_interest_paise", 0))
        other = deductions.get("other_eligible_deductions_paise", 0)
        eligible_deductions = sec_80c + sec_80d + sec_80ccd + hra + home_loan + other
    else:
        # New regime: no deductions except standard deduction
        eligible_deductions = 0

    taxable_income = max(0, after_std - eligible_deductions)

    # Slab-wise marginal tax
    income_tax = _slab_tax(taxable_income, slab_list)

    # Rebate (Section 87A) - only if income below threshold
    rebate_limit = regime_rules.get("rebate_limit_paise", 0)
    rebate_max_income = regime_rules.get("rebate_max_income_paise", 0)
    rebate_applied = 0
    if rebate_limit > 0 and taxable_income <= rebate_max_income:
        rebate_applied = min(income_tax, rebate_limit)
    income_tax_after_rebate = max(0, income_tax - rebate_applied)

    # Surcharge
    surcharge = _apply_surcharge(income_tax_after_rebate, gross_income_paise, surcharge_thresholds)

    # Cess after tax and rebate treatment
    cess = int((income_tax_after_rebate + surcharge) * cess_bp / 10000)

    total_tax = income_tax_after_rebate + surcharge + cess

    return RegimeResult(
        gross_income_paise=gross_income_paise,
        standard_deduction_paise=std_deduction,
        eligible_deductions_paise=eligible_deductions,
        taxable_income_paise=taxable_income,
        income_tax_paise=income_tax_after_rebate,
        cess_paise=cess,
        surcharge_paise=surcharge,
        total_tax_paise=total_tax,
        rebate_applied_paise=rebate_applied,
    )


def compare_tax_regimes(
    financial_year: str,
    annual_salary_paise: int,
    deductions: dict,
) -> TaxComparisonResult:
    """Compare old vs new tax regime for the given financial year.

    Raises ValueError if the financial year's rules are unavailable.
    """
    rules = _load_rules()

    if rules["financial_year"] != financial_year:
        raise ValueError(
            f"Tax rules for financial year '{financial_year}' are not available. "
            f"Only '{rules['financial_year']}' is supported."
        )

    old = _calculate_regime(annual_salary_paise, deductions, "old", rules)
    new = _calculate_regime(annual_salary_paise, deductions, "new", rules)

    lower = "old" if old.total_tax_paise <= new.total_tax_paise else "new"
    savings = abs(old.total_tax_paise - new.total_tax_paise)

    metadata = {
        "financial_year": rules["financial_year"],
        "rule_version": rules.get("rule_version"),
        "source_reference": rules.get("source_reference"),
        "last_verified_date": rules.get("last_verified_date"),
        "verification_status": rules.get("verification_status"),
    }

    return TaxComparisonResult(
        financial_year=financial_year,
        gross_salary_paise=annual_salary_paise,
        old_regime=old,
        new_regime=new,
        lower_tax_regime=lower,
        estimated_savings_paise=savings,
        disclaimer=rules.get(
            "disclaimer",
            "This is an illustrative estimate, not professional tax advice. Verify current Income Tax Department rules.",
        ),
        rules_metadata=metadata,
    )
