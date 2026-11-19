"""Nudge repository — user-scoped database operations for nudges."""

from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.nudge import Nudge


class NudgeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, **kwargs) -> Nudge:
        nudge = Nudge(user_id=user_id, **kwargs)
        self.db.add(nudge)
        self.db.flush()
        return nudge

    def get(self, nudge_id: str, user_id: str) -> Optional[Nudge]:
        return (
            self.db.query(Nudge)
            .filter(Nudge.id == nudge_id, Nudge.user_id == user_id)
            .first()
        )

    def list(self, user_id: str) -> Tuple[List[Nudge], int]:
        query = self.db.query(Nudge).filter(Nudge.user_id == user_id)
        total = query.count()
        items = query.order_by(Nudge.created_at.desc()).all()
        return items, total

    def find_by_dedupe_key(self, user_id: str, dedupe_key: str) -> Optional[Nudge]:
        return (
            self.db.query(Nudge)
            .filter(Nudge.user_id == user_id, Nudge.dedupe_key == dedupe_key)
            .first()
        )

    def count_in_window(
        self, user_id: str, from_datetime, to_datetime
    ) -> int:
        return (
            self.db.query(Nudge)
            .filter(
                Nudge.user_id == user_id,
                Nudge.created_at >= from_datetime,
                Nudge.created_at <= to_datetime,
            )
            .count()
        )

    def mark_read(self, nudge_id: str, user_id: str) -> Optional[Nudge]:
        nudge = self.get(nudge_id, user_id)
        if nudge is None:
            return None
        nudge.status = "read"
        self.db.flush()
        return nudge

    def mark_dismissed(self, nudge_id: str, user_id: str) -> Optional[Nudge]:
        nudge = self.get(nudge_id, user_id)
        if nudge is None:
            return None
        nudge.status = "dismissed"
        self.db.flush()
        return nudge
