"""Dues API routes — CONTRACT.md §7."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import DbSession, get_current_user
from app.models.due import Due
from app.models.user import User
from app.repositories.due_repository import DueRepository
from app.schemas.due import (
    DueCreate,
    DueItem,
    DueList,
    DueUpdate,
    MarkPaidRequest,
    MarkPaidResponse,
)
from app.utils.dates import parse_date_iso

router = APIRouter()


def _due_to_item(due: Due) -> DueItem:
    return DueItem(
        id=due.id,
        title=due.title,
        due_type=due.due_type,
        amount_paise=due.amount_paise,
        due_date=due.due_date,
        frequency=due.frequency,
        status=due.status,
        is_mandatory=due.is_mandatory,
        confidence=due.confidence,
        source=due.source,
    )


@router.get(
    "/dues",
    response_model=DueList,
    tags=["dues"],
    summary="List dues",
)
def list_dues(
    db: DbSession,
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    """List the user's dues with optional status/date filtering."""
    repo = DueRepository(db)
    parsed_from = parse_date_iso(from_date) if from_date else None
    parsed_to = parse_date_iso(to_date) if to_date else None
    items, total = repo.list(
        user_id=current_user.id,
        status=status,
        from_date=parsed_from,
        to_date=parsed_to,
    )
    return DueList(items=[_due_to_item(d) for d in items], total=total)


@router.post(
    "/dues",
    response_model=DueItem,
    status_code=status.HTTP_201_CREATED,
    tags=["dues"],
    summary="Create a due",
)
def create_due(
    payload: DueCreate,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """Create a new manual due for the current user."""
    repo = DueRepository(db)
    due = repo.create(
        user_id=current_user.id,
        title=payload.title.strip(),
        due_type=payload.due_type,
        amount_paise=payload.amount_paise,
        due_date=payload.due_date,
        frequency=payload.frequency,
        status="upcoming",
        is_mandatory=payload.is_mandatory,
        confidence=1.0,
        source="manual",
    )
    return _due_to_item(due)


@router.patch(
    "/dues/{due_id}",
    response_model=DueItem,
    tags=["dues"],
    summary="Update a due",
)
def update_due(
    due_id: str,
    payload: DueUpdate,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """Partially update a due (user-scoped)."""
    repo = DueRepository(db)
    due = repo.get(due_id, current_user.id)
    if due is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Due not found",
        )
    if payload.amount_paise is not None:
        due.amount_paise = payload.amount_paise
    if payload.due_date is not None:
        due.due_date = payload.due_date
    if payload.status is not None:
        due.status = payload.status
    if payload.is_mandatory is not None:
        due.is_mandatory = payload.is_mandatory
    db.flush()
    return _due_to_item(due)


@router.post(
    "/dues/{due_id}/mark-paid",
    response_model=MarkPaidResponse,
    tags=["dues"],
    summary="Mark a due as paid",
)
def mark_due_paid(
    due_id: str,
    payload: MarkPaidRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """Mark a due as paid (user-scoped)."""
    repo = DueRepository(db)
    due = repo.mark_paid(due_id, current_user.id, payload.paid_date)
    if due is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Due not found",
        )
    return MarkPaidResponse(
        id=due.id,
        status=due.status,
        paid_date=payload.paid_date,
    )
