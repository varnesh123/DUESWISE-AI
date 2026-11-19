"""Tax comparison API routes — CONTRACT.md §11.

Deterministic old/new regime calculations using configurable rules in
rules/tax_rules.json. AI is not involved in tax calculations.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import DbSession, get_current_user
from app.models.user import User
from app.schemas.tax import (
    DeductionsRequest,
    RegimeResult,
    RulesMetadata,
    TaxCompareRequest,
    TaxCompareResponse,
)
from app.services.tax_calculator import compare_tax_regimes

router = APIRouter()


def _regime_to_schema(regime) -> RegimeResult:
    return RegimeResult(
        gross_income_paise=regime.gross_income_paise,
        standard_deduction_paise=regime.standard_deduction_paise,
        eligible_deductions_paise=regime.eligible_deductions_paise,
        taxable_income_paise=regime.taxable_income_paise,
        income_tax_paise=regime.income_tax_paise,
        cess_paise=regime.cess_paise,
        surcharge_paise=regime.surcharge_paise,
        total_tax_paise=regime.total_tax_paise,
        rebate_applied_paise=regime.rebate_applied_paise,
    )


@router.post(
    "/tax/compare",
    response_model=TaxCompareResponse,
    tags=["tax"],
    summary="Compare old vs new tax regime",
)
def compare_tax(
    payload: TaxCompareRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """Compare tax payable under old and new regimes for the given financial year.

    Uses configurable rules from rules/tax_rules.json. If the requested financial
    year's rules are unavailable, returns a 422 unsupported-rules error.
    """
    try:
        result = compare_tax_regimes(
            financial_year=payload.financial_year,
            annual_salary_paise=payload.annual_salary_paise,
            deductions=payload.deductions.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    return TaxCompareResponse(
        financial_year=result.financial_year,
        gross_salary_paise=result.gross_salary_paise,
        old_regime=_regime_to_schema(result.old_regime),
        new_regime=_regime_to_schema(result.new_regime),
        lower_tax_regime=result.lower_tax_regime,
        estimated_savings_paise=result.estimated_savings_paise,
        disclaimer=result.disclaimer,
        rules_metadata=RulesMetadata(
            financial_year=result.rules_metadata["financial_year"],
            rule_version=result.rules_metadata.get("rule_version"),
            source_reference=result.rules_metadata.get("source_reference"),
            last_verified_date=result.rules_metadata.get("last_verified_date"),
            verification_status=result.rules_metadata.get("verification_status"),
        ),
    )
