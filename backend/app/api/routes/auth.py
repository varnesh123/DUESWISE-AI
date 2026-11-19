"""Authentication routes — CONTRACT.md §3 (demo session).

Synthetic demo-session mechanism for the hackathon MVP. Not production auth.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import DbSession, DEMO_USERS, get_current_user
from app.models.user import User
from app.schemas.auth import DemoRequest, DemoResponse, DemoUser, UserResponse

router = APIRouter()


def _ensure_demo_user(db: DbSession, persona: str) -> User:
    """Get or create the deterministic demo user for a persona."""
    profile = DEMO_USERS.get(persona)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown persona: {persona}. Use one of: {', '.join(DEMO_USERS)}",
        )
    user = db.query(User).filter(User.id == profile["id"]).first()
    if user is None:
        user = User(
            id=profile["id"],
            name=profile["name"],
            persona=profile["persona"],
            currency=profile["currency"],
        )
        db.add(user)
        db.flush()
    return user


@router.post(
    "/auth/demo",
    response_model=DemoResponse,
    tags=["auth"],
    summary="Create demo session",
)
def demo_session(request: DemoRequest, db: DbSession):
    """Create a synthetic demo session for the given persona.

    Returns a deterministic user and opaque bearer token (the user UUID).
    """
    user = _ensure_demo_user(db, request.persona)
    return DemoResponse(
        user=DemoUser(
            id=user.id,
            name=user.name,
            persona=user.persona,
            currency=user.currency,
        ),
        access_token=user.id,
        token_type="bearer",
    )


@router.get(
    "/auth/me",
    response_model=UserResponse,
    tags=["auth"],
    summary="Get current user",
)
def auth_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated demo user."""
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        persona=current_user.persona,
        currency=current_user.currency,
    )
