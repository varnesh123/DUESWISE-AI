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


class AAMockRequest(BaseModel):
    consent_id: str = Field(..., description="Mock consent identifier")
    account_reference: str = Field(..., description="Mock account reference")


class AAMockResponse(BaseModel):
    status: str
    source: str = "aa_mock"
    imported_count: int
    duplicates_skipped: int = 0
