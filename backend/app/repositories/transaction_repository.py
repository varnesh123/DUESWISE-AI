"""Transaction repository — user-scoped database operations.

All queries are filtered by user_id to guarantee data isolation.
"""

from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, **kwargs) -> Transaction:
        txn = Transaction(user_id=user_id, **kwargs)
        self.db.add(txn)
        self.db.flush()
        return txn

    def get(self, transaction_id: str, user_id: str) -> Optional[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(Transaction.id == transaction_id, Transaction.user_id == user_id)
            .first()
        )

    def update(self, transaction_id: str, user_id: str, **fields) -> Optional[Transaction]:
        """Apply user-scoped updates and return the transaction (or None)."""
        txn = self.get(transaction_id, user_id)
        if txn is None:
            return None
        for key, value in fields.items():
            setattr(txn, key, value)
        self.db.flush()
        return txn

    def delete(self, transaction_id: str, user_id: str) -> bool:
        """Delete a transaction owned by the user. Returns False if not found."""
        txn = self.get(transaction_id, user_id)
        if txn is None:
            return False
        self.db.delete(txn)
        self.db.flush()
        return True

    def find_duplicate(
        self,
        user_id: str,
        amount_paise: int,
        transaction_date: date,
        transaction_type: str,
        merchant_normalized: str,
        payment_method: str,
        source: str,
        source_reference: Optional[str] = None,
    ) -> Optional[Transaction]:
        """Find an existing transaction that matches this one.

        Uses source_reference when available; otherwise matches on the stable
        fingerprint: user_id + amount + date + type + normalised merchant +
        payment method + source.
        """
        if source_reference:
            existing = (
                self.db.query(Transaction)
                .filter(
                    Transaction.user_id == user_id,
                    Transaction.source == source,
                    Transaction.source_reference == source_reference,
                )
                .first()
            )
            if existing:
                return existing

        return (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.amount_paise == amount_paise,
                Transaction.transaction_date == transaction_date,
                Transaction.transaction_type == transaction_type,
                Transaction.merchant_normalized == merchant_normalized,
                Transaction.payment_method == payment_method,
            )
            .first()
        )

    def list(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        transaction_type: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Transaction], int]:
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)

        if category:
            query = query.filter(Transaction.category == category)
        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)
        if from_date:
            query = query.filter(Transaction.transaction_date >= from_date)
        if to_date:
            query = query.filter(Transaction.transaction_date <= to_date)
        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(
                    Transaction.merchant_raw.ilike(like),
                    Transaction.merchant_normalized.ilike(like),
                )
            )

        total = query.count()
        items = (
            query.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total
