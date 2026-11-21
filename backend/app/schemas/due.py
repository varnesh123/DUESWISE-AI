"""Due schemas — CONTRACT.md §7."""

from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class DueBase(BaseModel):
    title: str = Field(..., description="Title of the due")
    due_type: str = Field(..., description="rent/emi/insurance/utility/credit_card/subscription/other")
    amount_paise: int = Field(..., ge=0, description="Amount in integer paise")
    due_date: date = Field(..., description="Due date YYYY-MM-DD")
    frequency: str = Field(..., description="one_time/weekly/monthly/quarterly/yearly")
    is_mandatory: bool = Field(True, description="Whether the due is mandatory")


class DueCreate(DueBase):
    pass


class DueItem(BaseModel):
    id: str
    title: str
    due_type: str
    amount_paise: int
    due_date: date
    frequency: str
    status: str
    is_mandatory: bool
    confidence: float
    source: str


class DueList(BaseModel):
    items: List[DueItem]
    total: int


class DueUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    due_type: Optional[str] = Field(
        None, description="rent/emi/insurance/utility/credit_card/subscription/other"
    )
    amount_paise: Optional[int] = Field(None, ge=0)
    due_date: Optional[date] = None
    frequency: Optional[str] = Field(
        None, description="one_time/weekly/monthly/quarterly/yearly"
    )
    status: Optional[str] = None
    is_mandatory: Optional[bool] = None


class MarkPaidRequest(BaseModel):
    paid_date: date


class MarkPaidResponse(BaseModel):
    id: str
    status: str
    paid_date: date
