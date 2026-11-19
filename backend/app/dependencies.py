"""FastAPI dependencies — database session and current user resolution."""

from typing import Annotated, Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User

DbSession = Annotated[Session, Depends(get_db)]

# Deterministic demo users keyed by persona. These are synthetic and only for
# the hackathon MVP — production authentication is a roadmap item.
DEMO_USERS = {
    "salaried": {
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "Aarav Sharma",
        "persona": "salaried",
        "currency": "INR",
    },
    "young_professional": {
        "id": "22222222-2222-4222-8222-222222222222",
        "name": "Priya Patel",
        "persona": "young_professional",
        "currency": "INR",
    },
    "shopkeeper": {
        "id": "33333333-3333-4333-8333-333333333333",
        "name": "Rajesh Kumar",
        "persona": "shopkeeper",
        "currency": "INR",
    },
}


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the Bearer demo token.

    The demo token is the user's UUID. All protected endpoints require this.
    Returns 401 when the header is missing or the user is not found.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication",
        )
    parts = authorization.split(" ", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication",
        )
    token = parts[1].strip()
    user = db.query(User).filter(User.id == token).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication",
        )
    return user
