"""
MediRisk 2.0 — FastAPI Dependencies
Phase 4: Backend Core

Reusable dependency functions for:
  - database session
  - JWT authentication
  - RBAC (role-based access)
  - rate limiter
"""

import logging
from typing import Annotated, Optional

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.repositories.repositories import UserRepository

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database dependency (re-export for convenience)
# ---------------------------------------------------------------------------
DBSession = Annotated[AsyncSession, Depends(get_db)]

# ---------------------------------------------------------------------------
# JWT bearer scheme
# ---------------------------------------------------------------------------
_bearer = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(_bearer)
    ] = None,
) -> str:
    """
    Extract and validate the JWT bearer token.
    Returns the user UUID (str) encoded in the 'sub' claim.
    Raises AuthenticationError on missing / invalid / expired token.

    NOTE: Full login/registration is implemented in Phase 5.
          This dependency is the reusable auth gate for protected endpoints.
    """
    if credentials is None:
        raise AuthenticationError("No authentication token provided.")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload["sub"]
        return user_id
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired.")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token.")


CurrentUserId = Annotated[str, Depends(get_current_user_id)]


async def get_current_active_user(
    user_id: CurrentUserId,
    db: DBSession,
):
    """
    Resolve the JWT sub claim to a full User ORM object.
    Raises 401 if user does not exist or is inactive.
    """
    import uuid as _uuid

    repo = UserRepository(db)
    try:
        uid = _uuid.UUID(user_id)
    except ValueError:
        raise AuthenticationError("Invalid token subject.")

    user = await repo.get_by_id(uid)
    if user is None or not user.is_active:
        raise AuthenticationError("User account not found or inactive.")
    return user


# ---------------------------------------------------------------------------
# RBAC — role dependency factory
# ---------------------------------------------------------------------------

def require_role(*required_roles: str):
    """
    Dependency factory: ensures the current user has at least one of the
    listed roles (e.g. require_role("admin")).

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
    """

    async def _check_roles(
        current_user=Depends(get_current_active_user),
    ):
        user_role_names = {ur.role.name for ur in (current_user.user_roles or [])}
        if not user_role_names.intersection(set(required_roles)):
            raise AuthorizationError(
                f"One of these roles is required: {', '.join(required_roles)}"
            )
        return current_user

    return _check_roles


# ---------------------------------------------------------------------------
# Rate limiter instance (slowapi)
# ---------------------------------------------------------------------------
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
