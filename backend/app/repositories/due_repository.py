"""Due repository — user-scoped database operations for dues."""

from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.due import Due


class DueRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, **kwargs) -> Due:
        due = Due(user_id=user_id, **kwargs)
        self.db.add(due)
        self.db.flush()
        return due

    def get(self, due_id: str, user_id: str) -> Optional[Due]:
        return (
            self.db.query(Due)
            .filter(Due.id == due_id, Due.user_id == user_id)
            .first()
        )

    def list(
        self,
        user_id: str,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Tuple[List[Due], int]:
        query = self.db.query(Due).filter(Due.user_id == user_id)

        if status:
            query = query.filter(Due.status == status)
        if from_date:
            query = query.filter(Due.due_date >= from_date)
        if to_date:
            query = query.filter(Due.due_date <= to_date)

        total = query.count()
        items = query.order_by(Due.due_date.asc(), Due.created_at.desc()).all()
        return items, total

    def get_upcoming_mandatory(
        self,
        user_id: str,
        from_date: date,
        through_date: date,
    ) -> List[Due]:
        """Return unpaid mandatory dues due within [from_date, through_date]."""
        return (
            self.db.query(Due)
            .filter(
                Due.user_id == user_id,
                Due.is_mandatory == True,  # noqa: E712
                Due.status.in_(("upcoming", "due")),
                Due.due_date >= from_date,
                Due.due_date <= through_date,
            )
            .all()
        )

    def mark_paid(self, due_id: str, user_id: str, paid_date: date) -> Optional[Due]:
        due = self.get(due_id, user_id)
        if due is None:
            return None
        due.status = "paid"
        self.db.flush()
        return due
