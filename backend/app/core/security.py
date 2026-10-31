"""
MediRisk 2.0 — Security Utilities
Phase 4: Backend Core

Provides:
  - Argon2id password hashing via pwdlib
  - JWT creation / decoding via PyJWT
  - No passlib, no python-jose
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing (Argon2id via pwdlib)
# ---------------------------------------------------------------------------

_password_hasher = PasswordHash([Argon2Hasher()])


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password with Argon2id. Returns the full hash string."""
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored Argon2id hash.
    Returns True when they match, False otherwise.
    """
    try:
        return _password_hasher.verify(plain_password, hashed_password)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT utilities (PyJWT)
# ---------------------------------------------------------------------------

# Token type constants
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def create_access_token(
    subject: str,
    *,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: The token subject (user UUID as string).
        expires_delta: Override default expiry. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.
        extra_claims: Additional claims to embed (e.g. roles).

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "type": TOKEN_TYPE_ACCESS,
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a signed JWT refresh token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "type": TOKEN_TYPE_REFRESH,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Returns the full payload dict on success.

    Raises:
        jwt.ExpiredSignatureError   — token has expired
        jwt.InvalidTokenError       — token is malformed or signature invalid
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "exp", "iat", "jti", "type"]},
    )
    if payload.get("type") != TOKEN_TYPE_ACCESS:
        raise InvalidTokenError("Token type is not 'access'")
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT refresh token."""
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "exp", "iat", "jti", "type"]},
    )
    if payload.get("type") != TOKEN_TYPE_REFRESH:
        raise InvalidTokenError("Token type is not 'refresh'")
    return payload
