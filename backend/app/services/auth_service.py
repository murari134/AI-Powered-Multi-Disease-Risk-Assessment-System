"""
MediRisk 2.0 — Authentication Service
Phase 5: Authentication API

Orchestrates: registration, login, token issuance, refresh rotation, logout.
No HTTP concerns — callable from endpoints or tests.
No ML, no TabPFN, no inference.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
)
from app.core.security import hash_password, verify_password
from app.core.token_service import (
    access_token_expires_in,
    extract_jti,
    hash_token,
    make_access_token,
    make_refresh_token,
    refresh_token_expiry,
    validate_refresh_token,
)
from app.models.models import RefreshToken, Role, User, UserRole
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.repositories import RoleRepository, UserRepository
from app.schemas.auth_schemas import (
    LoginRequest,
    LogoutResponse,
    RefreshResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.services import AuditService

logger = logging.getLogger(__name__)

# Safe audit metadata fields — NEVER include passwords or tokens
_SAFE_AUDIT_FIELDS = frozenset({"event", "success", "request_id", "ip", "user_agent"})


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.role_repo = RoleRepository(session)
        self.rt_repo = RefreshTokenRepository(session)
        self.audit = AuditService(session)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalize_email(self, email: str) -> str:
        """Lowercase + strip. Consistent normalisation before DB lookups."""
        return email.strip().lower()

    async def _get_user_with_roles(self, user_id: uuid.UUID) -> Optional[User]:
        """Load user with eagerly-loaded user_roles + role."""
        from sqlalchemy import select

        result = await self.session.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role)
            )
        )
        return result.scalar_one_or_none()

    def _get_role_names(self, user: User) -> list[str]:
        return [ur.role.name for ur in (user.user_roles or []) if ur.role]

    async def _issue_token_pair(self, user: User) -> tuple[str, str, RefreshToken]:
        """Issue (access_token, refresh_token) and persist the refresh record."""
        roles = self._get_role_names(user)
        access_token = make_access_token(str(user.id), roles)
        raw_refresh = make_refresh_token(str(user.id))

        payload = validate_refresh_token(raw_refresh)
        jti = extract_jti(payload)
        token_hash = hash_token(raw_refresh)
        expires_at = refresh_token_expiry()

        record = RefreshToken(
            id=uuid.uuid4(),
            user_id=user.id,
            token_jti=jti,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(record)
        await self.session.flush()
        return access_token, raw_refresh, record

    # ------------------------------------------------------------------
    # Register
    # ------------------------------------------------------------------

    async def register(
        self,
        data: RegisterRequest,
        *,
        request_id: str = "-",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserResponse:
        normalized_email = self._normalize_email(data.email)

        # Check duplicate before hashing (fast path)
        if await self.user_repo.email_exists(normalized_email):
            await self.audit.log_event(
                "USER_REGISTER_DUPLICATE",
                event_metadata={"event": "register", "success": False, "request_id": request_id},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise ConflictError(f"An account with this email already exists.")

        # Assign default USER role
        user_role = await self.role_repo.get_by_name("user")
        if user_role is None:
            logger.error("'user' role not found — run seed_roles.py")
            raise ServiceUnavailableError("Role configuration")

        user = User(
            id=uuid.uuid4(),
            email=normalized_email,
            password_hash=hash_password(data.password),
            is_active=True,
        )
        self.session.add(user)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError("An account with this email already exists.")

        # Assign role
        assoc = UserRole(user_id=user.id, role_id=user_role.id)
        self.session.add(assoc)
        await self.session.flush()
        await self.session.commit()

        # Reload with roles
        full_user = await self._get_user_with_roles(user.id)

        await self.audit.log_event(
            "USER_REGISTERED",
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            event_metadata={"event": "register", "success": True, "request_id": request_id},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return UserResponse.from_orm_user(full_user)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    async def login(
        self,
        data: LoginRequest,
        *,
        request_id: str = "-",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenResponse:
        normalized_email = self._normalize_email(data.email)
        _SAFE_MSG = "Invalid credentials."  # same message for all failures

        user = await self.user_repo.get_by_email(normalized_email)

        if user is None or not verify_password(data.password, user.password_hash):
            await self.audit.log_event(
                "USER_LOGIN_FAILED",
                user_id=user.id if user else None,
                event_metadata={"event": "login", "success": False, "request_id": request_id},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise AuthenticationError(_SAFE_MSG)

        if not user.is_active:
            await self.audit.log_event(
                "USER_LOGIN_INACTIVE",
                user_id=user.id,
                event_metadata={"event": "login", "success": False, "reason": "inactive", "request_id": request_id},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise AuthenticationError(_SAFE_MSG)

        full_user = await self._get_user_with_roles(user.id)
        access_token, raw_refresh, _ = await self._issue_token_pair(full_user)
        await self.session.commit()

        await self.audit.log_event(
            "USER_LOGIN_SUCCESS",
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            event_metadata={"event": "login", "success": True, "request_id": request_id},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in=access_token_expires_in(),
        )

    # ------------------------------------------------------------------
    # Refresh (with rotation)
    # ------------------------------------------------------------------

    async def refresh(
        self,
        raw_refresh_token: str,
        *,
        request_id: str = "-",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RefreshResponse:
        try:
            payload = validate_refresh_token(raw_refresh_token)
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Refresh token has expired.")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid refresh token.")

        jti = extract_jti(payload)
        record = await self.rt_repo.get_by_jti(jti)

        if record is None or not record.is_valid:
            raise AuthenticationError("Refresh token is invalid or has been revoked.")

        # Validate hash matches (tamper detection)
        if hash_token(raw_refresh_token) != record.token_hash:
            # Possible token forgery — revoke everything for this user
            await self.rt_repo.revoke_all_for_user(record.user_id)
            await self.session.commit()
            raise AuthenticationError("Refresh token integrity check failed.")

        user = await self._get_user_with_roles(record.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User account not found or inactive.")

        # Rotation: revoke old record and issue new pair
        record.revoked_at = datetime.now(timezone.utc)
        await self.session.flush()

        new_access, new_refresh, _ = await self._issue_token_pair(user)
        await self.session.commit()

        await self.audit.log_event(
            "TOKEN_REFRESHED",
            user_id=user.id,
            event_metadata={"event": "refresh", "success": True, "request_id": request_id},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return RefreshResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=access_token_expires_in(),
        )

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    async def logout(
        self,
        raw_refresh_token: str,
        *,
        user_id: Optional[uuid.UUID] = None,
        request_id: str = "-",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> LogoutResponse:
        try:
            payload = validate_refresh_token(raw_refresh_token)
            jti = extract_jti(payload)
        except jwt.InvalidTokenError:
            # Even on bad token, return success — client is logging out
            return LogoutResponse()

        revoked = await self.rt_repo.revoke_by_jti(jti)
        await self.session.commit()

        await self.audit.log_event(
            "USER_LOGOUT",
            user_id=user_id,
            event_metadata={"event": "logout", "success": True, "revoked": revoked, "request_id": request_id},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return LogoutResponse()

    # ------------------------------------------------------------------
    # Current user
    # ------------------------------------------------------------------

    async def get_current_user(self, user_id: uuid.UUID) -> UserResponse:
        user = await self._get_user_with_roles(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User account not found or inactive.")
        return UserResponse.from_orm_user(user)
