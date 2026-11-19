"""Subscriptions API routes — CONTRACT.md §8."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import DbSession, get_current_user
from app.models.subscription import Subscription
from app.models.user import User
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.subscription import (
    SubscriptionItem,
    SubscriptionList,
    SubscriptionConfirmResponse,
    SubscriptionDismissResponse,
)

router = APIRouter()


def _sub_to_item(sub: Subscription) -> SubscriptionItem:
    return SubscriptionItem(
        id=sub.id,
        merchant=sub.merchant,
        category=sub.category,
        expected_amount_paise=sub.expected_amount_paise,
        frequency=sub.frequency,
        next_due_date=sub.next_due_date,
        detection_confidence=sub.detection_confidence,
        status=sub.status,
        is_user_confirmed=sub.is_user_confirmed,
    )


@router.get(
    "/subscriptions",
    response_model=SubscriptionList,
    tags=["subscriptions"],
    summary="List subscriptions",
)
def list_subscriptions(
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """List the user's subscriptions."""
    repo = SubscriptionRepository(db)
    items, total = repo.list(user_id=current_user.id)
    return SubscriptionList(items=[_sub_to_item(s) for s in items], total=total)


@router.post(
    "/subscriptions/{subscription_id}/confirm",
    response_model=SubscriptionConfirmResponse,
    tags=["subscriptions"],
    summary="Confirm a subscription",
)
def confirm_subscription(
    subscription_id: str,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """Confirm a detected subscription, moving it from uncertain to active."""
    repo = SubscriptionRepository(db)
    sub = repo.confirm(subscription_id, current_user.id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    return SubscriptionConfirmResponse(
        id=sub.id,
        status=sub.status,
        is_user_confirmed=sub.is_user_confirmed,
    )


@router.post(
    "/subscriptions/{subscription_id}/dismiss",
    response_model=SubscriptionDismissResponse,
    tags=["subscriptions"],
    summary="Dismiss a subscription",
)
def dismiss_subscription(
    subscription_id: str,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """Dismiss a detected subscription, moving it to cancelled."""
    repo = SubscriptionRepository(db)
    sub = repo.dismiss(subscription_id, current_user.id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    return SubscriptionDismissResponse(id=sub.id, status=sub.status)
