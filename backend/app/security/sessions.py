"""Opaque session-token helpers.

A session token is a high-entropy random string returned to the client once.
Only a SHA-256 digest of the token is stored server-side, so a database leak
does not expose usable bearer tokens.
"""

from __future__ import annotations

import hashlib
import secrets
import time

_TOKEN_BYTES = 32

# Default lifetime for a signed-in session (7 days). Overridable via settings.
DEFAULT_SESSION_TTL_MINUTES = 60 * 24 * 7


def generate_session_token() -> str:
    """Return a new URL-safe opaque bearer token."""
    return secrets.token_urlsafe(_TOKEN_BYTES)


def hash_session_token(token: str) -> str:
    """Return the hex SHA-256 digest stored in the database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_expiry_epoch(ttl_minutes: int = DEFAULT_SESSION_TTL_MINUTES) -> int:
    """Return the Unix timestamp at which a new session expires."""
    return int(time.time()) + max(1, ttl_minutes) * 60
