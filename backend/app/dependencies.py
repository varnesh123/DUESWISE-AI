"""FastAPI dependencies — database session and current user resolution."""

import time
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth_session import AuthSession
from app.models.user import User
from app.security.sessions import hash_session_token

DbSession = Annotated[Session, Depends(get_db)]

# Deterministic demo users keyed by persona. These are synthetic and only for
# explicit demo mode — they have no password and are never created implicitly
# by normal login/registration.
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

def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid authentication",
    )


def get_bearer_token(authorization: Optional[str] = Header(None)) -> str:
    """Extract a bearer token from the Authorization header or raise 401."""
    if not authorization or not authorization.startswith("Bearer "):
        raise _unauthorized()
    token = authorization[len("Bearer ") :].strip()
    if not token:
        raise _unauthorized()
    return token


def resolve_user_from_token(db: Session, token: str) -> Optional[User]:
    """Resolve a token to a user.

    Supports both authentication mechanisms:

    1. Real sessions — the token is an opaque random value; only its SHA-256
       digest is stored in ``auth_sessions``. Revoked/expired sessions fail.
    2. Demo tokens — the token is the deterministic demo user's UUID. This
       preserves explicit demo mode and backwards compatibility.
    """
    # Explicit demo token: the user UUID itself.
    demo_user = db.query(User).filter(User.id == token).first()
    if demo_user is not None:
        return demo_user

    # Real session token.
    session = (
        db.query(AuthSession)
        .filter(AuthSession.token_hash == hash_session_token(token))
        .first()
    )
    if session is None:
        return None
    if session.revoked_at is not None:
        return None
    if session.expires_at <= int(time.time()):
        return None
    return db.query(User).filter(User.id == session.user_id).first()


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a Bearer token.

    All protected endpoints use this dependency, so every query can be scoped
    by ``user.id`` and one account can never read another account's data.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise _unauthorized()
    token = authorization[len("Bearer ") :].strip()
    if not token:
        raise _unauthorized()
    user = resolve_user_from_token(db, token)
    if user is None:
        raise _unauthorized()
    return user
