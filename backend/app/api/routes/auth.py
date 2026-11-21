"""Authentication routes — CONTRACT.md §3.

Two intentionally separate paths:

- **Real accounts** (``/auth/register``, ``/auth/login``): passwords are hashed
  with PBKDF2-HMAC-SHA256 and a session token is stored hashed in the database.
- **Demo personas** (``/auth/demo``): deterministic synthetic users for the
  offline/demo experience. Demo mode is explicit and never used for normal
  login or registration.
"""

import re
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func

from app.config import settings
from app.dependencies import (
    DEMO_USERS,
    DbSession,
    get_bearer_token,
    get_current_user,
)
from app.models.auth_session import AuthSession
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    AuthUser,
    DemoRequest,
    DemoResponse,
    DemoUser,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.security.passwords import (
    hash_password,
    password_is_acceptable,
    verify_password,
)
from app.security.sessions import (
    generate_session_token,
    hash_session_token,
    session_expiry_epoch,
)

router = APIRouter()

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_email(email: str) -> str:
    normalized = (email or "").strip().lower()
    if not _EMAIL_RE.match(normalized):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enter a valid email address",
        )
    return normalized


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
            is_demo=True,
        )
        db.add(user)
        db.flush()
    return user


def _create_session(db: DbSession, user: User) -> str:
    """Create and persist a new opaque session token, returning the raw value."""
    token = generate_session_token()
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=hash_session_token(token),
            expires_at=session_expiry_epoch(settings.SESSION_TTL_MINUTES),
        )
    )
    db.flush()
    return token


def _auth_response(user: User, token: str) -> AuthResponse:
    return AuthResponse(
        user=AuthUser(
            id=user.id,
            name=user.name,
            email=user.email,
            persona=user.persona,
            currency=user.currency,
            is_demo=user.is_demo,
        ),
        user_id=user.id,
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.SESSION_TTL_MINUTES,
    )


@router.post(
    "/auth/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
    summary="Create a real account",
)
def register(request: RegisterRequest, db: DbSession):
    """Register a new account and sign in.

    The email is normalised to lowercase and must be unique. Passwords are
    never stored in plaintext. New accounts start with no financial records.
    """
    email = _normalize_email(request.email)
    if not password_is_acceptable(request.password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be between 8 and 128 characters",
        )
    name = request.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name is required",
        )

    existing = (
        db.query(User)
        .filter(func.lower(User.email) == email)
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(request.password),
        persona="individual",
        currency=request.currency.upper(),
        is_demo=False,
    )
    db.add(user)
    db.flush()

    token = _create_session(db, user)
    return _auth_response(user, token)


@router.post(
    "/auth/login",
    response_model=AuthResponse,
    tags=["auth"],
    summary="Sign in with email and password",
)
def login(request: LoginRequest, db: DbSession):
    """Authenticate a real account.

    Returns the same generic error for unknown email and wrong password so the
    endpoint does not reveal which accounts exist.
    """
    email = _normalize_email(request.email)
    user = (
        db.query(User)
        .filter(func.lower(User.email) == email)
        .first()
    )
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = _create_session(db, user)
    return _auth_response(user, token)


@router.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["auth"],
    summary="Sign out and revoke the current session",
)
def logout(
    db: DbSession,
    token: str = Depends(get_bearer_token),
    current_user: User = Depends(get_current_user),
):
    """Revoke the current session token.

    Demo tokens are deterministic and have no server-side session, so logout is
    a no-op for them.
    """
    session = (
        db.query(AuthSession)
        .filter(
            AuthSession.token_hash == hash_session_token(token),
            AuthSession.user_id == current_user.id,
        )
        .first()
    )
    if session is not None and session.revoked_at is None:
        session.revoked_at = int(time.time())
        db.flush()


@router.post(
    "/auth/demo",
    response_model=DemoResponse,
    tags=["auth"],
    summary="Create an explicit demo session",
)
def demo_session(request: DemoRequest, db: DbSession):
    """Create a synthetic demo session for the given persona.

    Explicit demo mode only. Normal login/registration never falls back here.
    """
    user = _ensure_demo_user(db, request.persona)
    return DemoResponse(
        user=DemoUser(
            id=user.id,
            name=user.name,
            email=user.email,
            persona=user.persona,
            currency=user.currency,
            is_demo=True,
        ),
        user_id=user.id,
        access_token=user.id,
        token_type="bearer",
        expires_in_minutes=30,
    )


@router.get(
    "/auth/me",
    response_model=UserResponse,
    tags=["auth"],
    summary="Get current user",
)
def auth_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        persona=current_user.persona,
        currency=current_user.currency,
        is_demo=current_user.is_demo,
    )
