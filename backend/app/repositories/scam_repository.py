"""Scam alert repository — user-scoped database operations for scam alerts."""

from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.scam_alert import ScamAlert


class ScamRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, **kwargs) -> ScamAlert:
        alert = ScamAlert(user_id=user_id, **kwargs)
        self.db.add(alert)
        self.db.flush()
        return alert

    def list(self, user_id: str) -> Tuple[List[ScamAlert], int]:
        query = self.db.query(ScamAlert).filter(ScamAlert.user_id == user_id)
        total = query.count()
        items = query.order_by(ScamAlert.created_at.desc()).all()
        return items, total
