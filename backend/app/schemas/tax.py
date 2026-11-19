"""Tax comparison schemas — CONTRACT.md §11."""

from typing import List, Optional
from pydantic import BaseModel, Field


class DeductionsRequest(BaseModel):
    section_80c_paise: int = Field(0, ge=0)
    section_80d_paise: int = Field(0, ge=0)
    section_80ccd_1b_paise: int = Field(0, ge=0)
    hra_exemption_paise: Optional[int] = Field(0, ge=0)
    home_loan_interest_paise: int = Field(0, ge=0)
    other_eligible_deductions_paise: int = Field(0, ge=0)


class TaxCompareRequest(BaseModel):
    financial_year: str = Field(..., description="e.g. FY-2025-26")
    annual_salary_paise: int = Field(..., ge=0, description="Annual salary in integer paise")
    deductions: DeductionsRequest


class RegimeResult(BaseModel):
    gross_income_paise: int
    standard_deduction_paise: int
    eligible_deductions_paise: int
    taxable_income_paise: int
    income_tax_paise: int
    cess_paise: int
    surcharge_paise: int
    total_tax_paise: int
    rebate_applied_paise: int = 0


class RulesMetadata(BaseModel):
    financial_year: str
    rule_version: Optional[str] = None
    source_reference: Optional[str] = None
    last_verified_date: Optional[str] = None
    verification_status: Optional[str] = None


class TaxCompareResponse(BaseModel):
    financial_year: str
    gross_salary_paise: int
    old_regime: RegimeResult
    new_regime: RegimeResult
    lower_tax_regime: str
    estimated_savings_paise: int
    disclaimer: str
    rules_metadata: RulesMetadata
