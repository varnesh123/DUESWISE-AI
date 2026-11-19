"""Transaction API routes — CONTRACT.md §5.

All endpoints are user-scoped via the authenticated demo user.
Business logic lives in services/repositories; routes are thin.
"""

from datetime import date
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import DbSession, get_current_user
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.common import ErrorDetail, ErrorResponse
from app.schemas.transaction import (
    TransactionCreate,
    TransactionItem,
    TransactionList,
    TransactionFilters,
)
from app.utils.dates import parse_date_iso
from app.utils.money import validate_amount_paise
from app.models.user import User
from app.services.manual_transaction import (
    create_manual_transaction as create_manual_transaction_record,
)

router = APIRouter()


def _txn_to_item(txn) -> TransactionItem:
    return TransactionItem(
        id=txn.id,
        amount_paise=txn.amount_paise,
        currency=txn.currency,
        transaction_type=txn.transaction_type,
        merchant_raw=txn.merchant_raw,
        merchant_normalized=txn.merchant_normalized,
        category=txn.category,
        payment_method=txn.payment_method,
        payment_gateway=txn.payment_gateway,
        transaction_date=txn.transaction_date.isoformat(),
        source=txn.source,
        source_reference=txn.source_reference,
        confidence=txn.confidence,
        description=txn.description,
        is_suspicious=txn.is_suspicious,
    )


@router.get(
    "/transactions",
    response_model=TransactionList,
    tags=["transactions"],
    summary="List transactions",
)
def list_transactions(
    db: DbSession,
    current_user: User = Depends(get_current_user),
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    search: Optional[str] = None,
):
    """List the current user's transactions with pagination and filters."""
    repo = TransactionRepository(db)
    f = TransactionFilters(
        page=page,
        page_size=page_size,
        category=category,
        transaction_type=transaction_type,
        from_date=from_date,
        to_date=to_date,
        search=search,
    )
    parsed_from = parse_date_iso(f.from_date) if f.from_date else None
    parsed_to = parse_date_iso(f.to_date) if f.to_date else None
    items, total = repo.list(
        user_id=current_user.id,
        page=f.page,
        page_size=f.page_size,
        category=f.category,
        transaction_type=f.transaction_type,
        from_date=parsed_from,
        to_date=parsed_to,
        search=f.search,
    )
    return TransactionList(
        items=[_txn_to_item(t) for t in items],
        total=total,
        page=f.page,
        page_size=f.page_size,
    )


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionItem,
    tags=["transactions"],
    summary="Get a transaction by ID",
)
def get_transaction(
    transaction_id: str,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """Get a single transaction (user-scoped)."""
    repo = TransactionRepository(db)
    txn = repo.get(transaction_id, current_user.id)
    if txn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return _txn_to_item(txn)


@router.post(
    "/transactions/manual",
    response_model=TransactionItem,
    status_code=status.HTTP_201_CREATED,
    tags=["transactions"],
    summary="Create a manual transaction",
)
def create_manual_transaction(
    payload: TransactionCreate,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """Manually create a transaction for the current user."""
    validate_amount_paise(payload.amount_paise)
    try:
        txn_date = parse_date_iso(payload.transaction_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="transaction_date must be YYYY-MM-DD",
        )

    result = create_manual_transaction_record(
        db,
        user_id=current_user.id,
        amount_paise=payload.amount_paise,
        transaction_type=payload.transaction_type,
        merchant_raw=payload.merchant.strip(),
        merchant_normalized=payload.merchant.strip(),
        category=payload.category or "other",
        payment_method=payload.payment_method,
        transaction_date=txn_date,
    )
    if result.duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate transaction",
        )
    return _txn_to_item(result.transaction)
