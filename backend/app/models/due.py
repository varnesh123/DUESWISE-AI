"""Due model — blueprint §6 `dues` table.

Represents an upcoming obligation (rent, EMI, insurance, utility, credit card,
subscription, other). All monetary values stored as INTEGER paise. All data
scoped by user_id.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Due(Base):
    __tablename__ = "dues"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    due_type: Mapped[str] = mapped_column(String(50), nullable=False)  # rent/emi/insurance/utility/credit_card/subscription/other
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)  # one_time/weekly/monthly/quarterly/yearly
    status: Mapped[str] = mapped_column(String(20), default="upcoming", nullable=False)  # upcoming/due/paid/overdue
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)  # manual/detected
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
