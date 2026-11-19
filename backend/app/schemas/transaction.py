"""Transaction schemas — CONTRACT.md §5."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TransactionCreate(BaseModel):
    amount_paise: int = Field(..., ge=0, description="Amount in integer paise")
    transaction_type: str = Field(..., description="credit or debit")
    merchant: str = Field(..., description="Raw merchant name as provided by user")
    category: Optional[str] = Field(None, description="Optional category override")
    payment_method: str = Field(..., description="upi/card/net_banking/imps/neft/atm/cash/other")
    transaction_date: str = Field(..., description="Transaction date YYYY-MM-DD")


class TransactionItem(BaseModel):
    id: str
    amount_paise: int
    currency: str
    transaction_type: str
    merchant_raw: str
    merchant_normalized: str
    category: str
    payment_method: str
    payment_gateway: Optional[str] = None
    transaction_date: str
    source: str
    source_reference: Optional[str] = None
    confidence: float
    description: Optional[str] = None
    is_suspicious: bool


class TransactionList(BaseModel):
    items: List[TransactionItem]
    total: int
    page: int
    page_size: int


class TransactionFilters(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    category: Optional[str] = None
    transaction_type: Optional[str] = None  # credit/debit
    from_date: Optional[str] = None  # YYYY-MM-DD
    to_date: Optional[str] = None  # YYYY-MM-DD
    search: Optional[str] = None  # merchant search
