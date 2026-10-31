"""
MediRisk 2.0 — Token Service
Phase 5: Authentication API

Centralised token creation, decoding, and hashing.
Keeps token handling separate from HTTP endpoints and services.
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings
from app.core.security import (
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)


# ---------------------------------------------------------------------------
# Re-export core token functions for use by AuthService
# ---------------------------------------------------------------------------
__all__ = [
    "make_access_token",
    "make_refresh_token",
    "validate_access_token",
    "validate_refresh_token",
    "hash_token",
    "extract_jti",
    "access_token_expires_in",
]


def make_access_token(user_id: str, roles: list[str] | None = None) -> str:
    """Create a signed JWT access token embedding the user's roles."""
    extra: dict[str, Any] = {}
    if roles:
        extra["roles"] = roles
    return create_access_token(user_id, extra_claims=extra)


def make_refresh_token(user_id: str) -> str:
    """Create a signed JWT refresh token."""
    return create_refresh_token(user_id)


def validate_access_token(token: str) -> dict[str, Any]:
    """Validate and decode an access token. Raises jwt.InvalidTokenError on failure."""
    return decode_access_token(token)


def validate_refresh_token(token: str) -> dict[str, Any]:
    """Validate and decode a refresh token. Raises jwt.InvalidTokenError on failure."""
    return decode_refresh_token(token)


def hash_token(raw_token: str) -> str:
    """
    Return a SHA-256 hex digest of the raw JWT string.
    Used to store a fingerprint of the refresh token without storing the token itself.
    """
    return hashlib.sha256(raw_token.encode()).hexdigest()


def extract_jti(payload: dict[str, Any]) -> str:
    """Extract the JTI claim from a decoded JWT payload."""
    jti = payload.get("jti")
    if not jti:
        raise InvalidTokenError("Token missing 'jti' claim.")
    return str(jti)


def access_token_expires_in() -> int:
    """Return access token TTL in seconds."""
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def refresh_token_expiry() -> datetime:
    """Return the UTC expiry datetime for a newly issued refresh token."""
    return datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
