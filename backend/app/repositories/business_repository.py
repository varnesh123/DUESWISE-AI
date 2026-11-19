"""Business entry repository — user-scoped database operations for business entries."""

from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.business import BusinessEntry


class BusinessRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, **kwargs) -> BusinessEntry:
        entry = BusinessEntry(user_id=user_id, **kwargs)
        self.db.add(entry)
        self.db.flush()
        return entry

    def list(self, user_id: str) -> Tuple[List[BusinessEntry], int]:
        query = self.db.query(BusinessEntry).filter(BusinessEntry.user_id == user_id)
        total = query.count()
        items = query.order_by(BusinessEntry.created_at.desc()).all()
        return items, total
