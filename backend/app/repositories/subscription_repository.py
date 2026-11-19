"""Subscription repository — user-scoped database operations for subscriptions."""

from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.subscription import Subscription


class SubscriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, **kwargs) -> Subscription:
        sub = Subscription(user_id=user_id, **kwargs)
        self.db.add(sub)
        self.db.flush()
        return sub

    def get(self, subscription_id: str, user_id: str) -> Optional[Subscription]:
        return (
            self.db.query(Subscription)
            .filter(Subscription.id == subscription_id, Subscription.user_id == user_id)
            .first()
        )

    def list(self, user_id: str) -> Tuple[List[Subscription], int]:
        query = self.db.query(Subscription).filter(Subscription.user_id == user_id)
        total = query.count()
        items = query.order_by(Subscription.next_due_date.asc(), Subscription.created_at.desc()).all()
        return items, total

    def confirm(self, subscription_id: str, user_id: str) -> Optional[Subscription]:
        sub = self.get(subscription_id, user_id)
        if sub is None:
            return None
        sub.status = "active"
        sub.is_user_confirmed = True
        self.db.flush()
        return sub

    def dismiss(self, subscription_id: str, user_id: str) -> Optional[Subscription]:
        sub = self.get(subscription_id, user_id)
        if sub is None:
            return None
        sub.status = "cancelled"
        self.db.flush()
        return sub
