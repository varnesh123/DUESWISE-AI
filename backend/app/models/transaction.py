"""Transaction model — blueprint §6 `transactions` table.

All monetary values are stored as INTEGER paise. All user data is scoped by
user_id. Externally visible IDs are UUID strings.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        # Helpful indexes for user-scoped lookups and deduplication
        {"extend_existing": True},
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)  # credit/debit
    merchant_raw: Mapped[str] = mapped_column(String(500), nullable=False)
    merchant_normalized: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_gateway: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # sms/csv/pdf/aa_mock/manual
    source_reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
