"""
MediRisk 2.0 — Authentication Endpoints
Phase 5: Authentication API

Routes:
  POST /api/v1/auth/register   — create account
  POST /api/v1/auth/login      — issue access + refresh tokens
  POST /api/v1/auth/refresh    — rotate refresh token → new access + refresh
  POST /api/v1/auth/logout     — revoke refresh token
  GET  /api/v1/auth/me         — current authenticated user

Rate limits (slowapi):
  /register: 10/minute
  /login:    20/minute
  /refresh:  30/minute
"""

import logging
import uuid
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.core.token_service import validate_access_token
from app.db.session import get_db
from app.dependencies import limiter
from app.schemas.auth_schemas import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

_bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "unknown")


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


async def _get_current_user_id_from_bearer(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ] = None,
) -> uuid.UUID:
    if credentials is None:
        raise AuthenticationError("No authentication token provided.")
    try:
        payload = validate_access_token(credentials.credentials)
        return uuid.UUID(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired.")
    except (jwt.InvalidTokenError, ValueError):
        raise AuthenticationError("Invalid token.")


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
@limiter.limit("10/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    user_resp = await svc.register(
        body,
        request_id=_get_request_id(request),
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )
    return RegisterResponse(user=user_resp)


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain access + refresh tokens",
)
@limiter.limit("20/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    return await svc.login(
        body,
        request_id=_get_request_id(request),
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )


# ---------------------------------------------------------------------------
# POST /refresh
# ---------------------------------------------------------------------------

@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Rotate refresh token and issue new access token",
)
@limiter.limit("30/minute")
async def refresh(
    request: Request,
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    return await svc.refresh(
        body.refresh_token,
        request_id=_get_request_id(request),
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------

@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Revoke refresh token and log out",
)
async def logout(
    request: Request,
    body: LogoutRequest,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ] = None,
    db: AsyncSession = Depends(get_db),
):
    current_user_id: uuid.UUID | None = None
    if credentials:
        try:
            payload = validate_access_token(credentials.credentials)
            current_user_id = uuid.UUID(payload["sub"])
        except Exception:
            pass  # logout proceeds even on expired/invalid access token

    svc = AuthService(db)
    return await svc.logout(
        body.refresh_token,
        user_id=current_user_id,
        request_id=_get_request_id(request),
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
)
async def me(
    user_id: Annotated[uuid.UUID, Depends(_get_current_user_id_from_bearer)],
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    return await svc.get_current_user(user_id)
