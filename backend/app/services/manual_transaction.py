"""Shared manual-transaction creation.

Both ``POST /transactions/manual`` and the manual branch of
``POST /transactions/ingest`` use this function so deduplication and
persistence live in exactly one place. Callers stay responsible for
validation and for deciding how the merchant is normalised and categorised.
"""

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository


@dataclass(frozen=True)
class ManualTransactionResult:
    """Outcome of a manual transaction attempt."""

    transaction: Transaction
    duplicate: bool


def create_manual_transaction(
    db: Session,
    *,
    user_id: str,
    amount_paise: int,
    transaction_type: str,
    merchant_raw: str,
    merchant_normalized: str,
    category: str,
    payment_method: str,
    transaction_date: date,
) -> ManualTransactionResult:
    """Create a manual transaction unless an identical one already exists.

    Duplicates are detected by amount, date, type, normalised merchant and
    payment method within the user's manual transactions. When a duplicate is
    found the existing transaction is returned with ``duplicate=True`` and
    nothing is written.
    """
    repo = TransactionRepository(db)

    existing = repo.find_duplicate(
        user_id=user_id,
        amount_paise=amount_paise,
        transaction_date=transaction_date,
        transaction_type=transaction_type,
        merchant_normalized=merchant_normalized,
        payment_method=payment_method,
        source="manual",
    )
    if existing is not None:
        return ManualTransactionResult(transaction=existing, duplicate=True)

    txn = repo.create(
        user_id=user_id,
        amount_paise=amount_paise,
        currency="INR",
        transaction_type=transaction_type,
        merchant_raw=merchant_raw,
        merchant_normalized=merchant_normalized,
        category=category,
        payment_method=payment_method,
        payment_gateway=None,
        transaction_date=transaction_date,
        source="manual",
        source_reference=None,
        confidence=1.0,
        description=None,
        is_suspicious=False,
    )
    return ManualTransactionResult(transaction=txn, duplicate=False)
