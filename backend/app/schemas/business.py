"""Small-business cash flow schemas — CONTRACT.md §12."""

from typing import List, Optional
from pydantic import BaseModel, Field


class BusinessEntryCreate(BaseModel):
    entry_type: str = Field(..., description="sale/expense/receivable/payable")
    description: str
    amount_paise: int = Field(..., ge=0)
    due_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    counterparty: Optional[str] = None


class BusinessEntryItem(BaseModel):
    id: str
    entry_type: str
    description: str
    amount_paise: int
    due_date: Optional[str] = None
    status: str
    counterparty: Optional[str] = None


class CashFlowRequest(BaseModel):
    current_cash_paise: int = Field(..., ge=0, description="Current cash balance in integer paise")
    forecast_date: str = Field(..., description="Forecast date YYYY-MM-DD")


class CashFlowItem(BaseModel):
    entry_type: str
    total_paise: int
    count: int


class CashFlowResponse(BaseModel):
    currency: str
    current_cash_paise: int
    total_sales_paise: int
    total_expenses_paise: int
    pending_receivables_paise: int
    pending_payables_paise: int
    projected_cash_balance_paise: int
    forecast_date: str
    items: List[CashFlowItem]


class InvoiceItem(BaseModel):
    description: str
    quantity: int = Field(..., ge=1)
    unit_price_paise: int = Field(..., ge=0)
    gst_rate_basis_points: int = Field(..., ge=0, description="GST rate in basis points (e.g. 1800 = 18%)")


class InvoiceRequest(BaseModel):
    invoice_number: str
    invoice_date: str
    customer_name: str
    customer_gstin: Optional[str] = None
    items: List[InvoiceItem]
    place_of_supply: str


class InvoiceResponse(BaseModel):
    invoice_number: str
    subtotal_paise: int
    cgst_paise: int
    sgst_paise: int
    igst_paise: int
    total_paise: int
    tax_calculation_status: str = "illustrative"
