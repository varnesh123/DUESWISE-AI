"""Nudges API routes — CONTRACT.md §9."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import DbSession, get_current_user
from app.models.nudge import Nudge
from app.models.user import User
from app.repositories.nudge_repository import NudgeRepository
from app.schemas.nudge import NudgeItem, NudgeList, NudgeActionResponse

router = APIRouter()


def _nudge_to_item(nudge: Nudge) -> NudgeItem:
    return NudgeItem(
        id=nudge.id,
        type=nudge.nudge_type,
        priority=nudge.priority,
        title=nudge.title,
        message=nudge.message,
        created_at=nudge.created_at,
        status=nudge.status,
        read=nudge.status == "read",
    )


@router.get(
    "/nudges",
    response_model=NudgeList,
    tags=["nudges"],
    summary="List nudges",
)
def list_nudges(
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """List the user's nudges."""
    repo = NudgeRepository(db)
    items, total = repo.list(user_id=current_user.id)
    return NudgeList(items=[_nudge_to_item(n) for n in items], total=total)


@router.post(
    "/nudges/{nudge_id}/read",
    response_model=NudgeActionResponse,
    tags=["nudges"],
    summary="Mark a nudge as read",
)
def mark_nudge_read(
    nudge_id: str,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    repo = NudgeRepository(db)
    nudge = repo.mark_read(nudge_id, current_user.id)
    if nudge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nudge not found",
        )
    return NudgeActionResponse(id=nudge.id, status=nudge.status)


@router.post(
    "/nudges/{nudge_id}/dismiss",
    response_model=NudgeActionResponse,
    tags=["nudges"],
    summary="Dismiss a nudge",
)
def mark_nudge_dismissed(
    nudge_id: str,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    repo = NudgeRepository(db)
    nudge = repo.mark_dismissed(nudge_id, current_user.id)
    if nudge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nudge not found",
        )
    return NudgeActionResponse(id=nudge.id, status=nudge.status)
