"""Password hashing utilities.

Uses PBKDF2-HMAC-SHA256 from the Python standard library so there is no extra
native dependency. Each password gets a fresh random salt; hashes are stored in
a self-describing ``algorithm$iterations$salt$hash`` format so parameters can be
upgraded later without breaking existing accounts.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 260_000
_SALT_BYTES = 16
_HASH_BYTES = 32

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def hash_password(password: str) -> str:
    """Return a salted PBKDF2 hash for *password*."""
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _ITERATIONS, dklen=_HASH_BYTES
    )
    return f"{_ALGORITHM}${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    """Return True when *password* matches *stored_hash*.

    Never raises for malformed stored values; a malformed hash simply fails
    verification. Uses a constant-time comparison for the digest.
    """
    if not password or not stored_hash:
        return False
    try:
        algorithm, iterations_text, salt_hex, digest_hex = stored_hash.split("$", 3)
        if algorithm != _ALGORITHM:
            return False
        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        return False
    if iterations <= 0 or not salt or not expected:
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations, dklen=len(expected)
    )
    return hmac.compare_digest(actual, expected)


def password_is_acceptable(password: str) -> bool:
    """Return whether a plaintext password meets the basic length policy."""
    return (
        isinstance(password, str)
        and MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH
    )
