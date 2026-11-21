"""User model.

Core identity table referenced by all user-scoped data. Externally visible IDs
are UUID strings; monetary values (where present later) use integer paise.
"""

from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    # PBKDF2 hash for real accounts. Demo personas have no password.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    persona: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    # Demo users are synthetic personas created by /auth/demo.
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
