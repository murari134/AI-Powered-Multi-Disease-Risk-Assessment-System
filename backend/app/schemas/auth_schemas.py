"""
MediRisk 2.0 — Authentication Schemas
Phase 5: Authentication API

All schemas use Pydantic v2.
password_hash is NEVER included in any response schema.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AuthBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Role response
# ---------------------------------------------------------------------------

class RoleResponse(AuthBase):
    id: uuid.UUID
    name: str


# ---------------------------------------------------------------------------
# User response  (never exposes password_hash)
# ---------------------------------------------------------------------------

class UserResponse(AuthBase):
    id: uuid.UUID
    email: str
    is_active: bool
    roles: list[RoleResponse] = Field(default_factory=list)
    created_at: datetime

    @classmethod
    def from_orm_user(cls, user) -> "UserResponse":
        """Build safe response from ORM User, loading roles through user_roles."""
        roles = [
            RoleResponse(id=ur.role.id, name=ur.role.name)
            for ur in (user.user_roles or [])
            if ur.role is not None
        ]
        return cls(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            roles=roles,
            created_at=user.created_at,
        )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class RegisterRequest(AuthBase):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password: minimum 8 characters.",
    )

    @field_validator("password")
    @classmethod
    def password_not_entirely_whitespace(cls, v: str) -> str:
        if v.strip() == "":
            raise ValueError("Password must not be blank.")
        return v


class RegisterResponse(AuthBase):
    user: UserResponse
    message: str = "Registration successful."


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class LoginRequest(AuthBase):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


# ---------------------------------------------------------------------------
# Token response
# ---------------------------------------------------------------------------

class TokenResponse(AuthBase):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token TTL in seconds")


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------

class RefreshRequest(AuthBase):
    refresh_token: str


class RefreshResponse(AuthBase):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class LogoutRequest(AuthBase):
    refresh_token: str


class LogoutResponse(AuthBase):
    message: str = "Logged out successfully. Refresh token has been revoked."
