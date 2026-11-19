"""Transaction ingestion schemas — CONTRACT.md §6."""

from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.transaction import TransactionItem


class SmsIngestRequest(BaseModel):
    message: str = Field(..., description="SMS message text to parse")
    source: str = Field("sms", description="Source label, always 'sms'")


class SmsIngestResponse(BaseModel):
    status: str
    transaction: Optional[TransactionItem] = None
    duplicate: bool = False
    warnings: List[str] = []


class FileIngestResponse(BaseModel):
    ingestion_id: str
    status: str
    imported_count: int
    rejected_count: int
    duplicates_skipped: int = 0
    errors: List[dict] = []


class UnifiedIngestRequest(BaseModel):
    """Contract path POST /transactions/ingest.

    Accepts either a manual transaction (merchant/amount/date) or a raw SMS
    ``message``, so a single client call covers both demo entry points.
    """

    merchant_raw: Optional[str] = Field(None, description="Merchant name as typed by the user")
    merchant: Optional[str] = Field(None, description="Alias for merchant_raw")
    amount_paise: Optional[int] = Field(None, ge=0, description="Amount in integer paise")
    transaction_type: str = Field("debit", description="credit or debit")
    category: Optional[str] = Field(None, description="Optional category override")
    payment_method: str = Field("other", description="Payment method label")
    transaction_date: Optional[str] = Field(None, description="YYYY-MM-DD; defaults to today (IST)")
    message: Optional[str] = Field(None, description="Raw SMS text instead of manual fields")


class UnifiedIngestResponse(BaseModel):
    status: str
    transaction: Optional[TransactionItem] = None
    duplicate: bool = False
    warnings: List[str] = []
    processing: dict = {}


class AAMockRequest(BaseModel):
    consent_id: str = Field(..., description="Mock consent identifier")
    account_reference: str = Field(..., description="Mock account reference")


class AAMockResponse(BaseModel):
    status: str
    source: str = "aa_mock"
    imported_count: int
    duplicates_skipped: int = 0
