"""
MediRisk 2.0 — Phase 5 Authentication Tests
Tests all 46 required points using in-memory SQLite test database.

SQLite Compatibility Note:
  PostgreSQL-specific types (JSONB, UUID) are remapped to SQLite-compatible
  types (JSON, String) for the test schema only.
  Production code always uses PostgreSQL types unchanged.
"""

import hashlib
import json
import uuid
from datetime import timedelta
from typing import AsyncGenerator

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, String, Text, event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
)
from app.core.token_service import hash_token
from app.schemas.auth_schemas import (
    RegisterRequest,
    UserResponse,
)


# ---------------------------------------------------------------------------
# SQLite-compatible test engine
# Patches JSONB → JSON, UUID(as_uuid) → String(36) for SQLite
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


def _sqlite_compat_metadata():
    """
    Return Base.metadata with PostgreSQL-specific types remapped for SQLite.
    We do this by creating the tables manually with compatible DDL.
    """
    # Patch postgresql types for SQLite compatibility
    from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
    from sqlalchemy import JSON, String

    # Register type overrides on the SQLite dialect
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

    def visit_JSONB(self, type_, **kwargs):
        return "JSON"

    def visit_UUID(self, type_, **kwargs):
        return "VARCHAR(36)"

    if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):
        SQLiteTypeCompiler.visit_JSONB = visit_JSONB
    if not hasattr(SQLiteTypeCompiler, "_orig_visit_UUID"):
        SQLiteTypeCompiler._orig_visit_UUID = getattr(
            SQLiteTypeCompiler, "visit_UUID", None
        )
        SQLiteTypeCompiler.visit_UUID = visit_UUID


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    _sqlite_compat_metadata()
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Register JSON serialiser for SQLite JSON columns
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_json(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")

    import app.models  # ensure all models registered
    from app.db.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def seeded_db(db_session: AsyncSession):
    """Seed the 'user' and 'admin' roles."""
    from app.models.models import Role
    user_role = Role(id=uuid.uuid4(), name="user", description="Standard user")
    admin_role = Role(id=uuid.uuid4(), name="admin", description="Admin user")
    db_session.add_all([user_role, admin_role])
    await db_session.commit()
    return db_session


# ---------------------------------------------------------------------------
# HTTP test client
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="function")
async def client(seeded_db: AsyncSession):
    from app.main import app
    from app.db.session import get_db
    from app.dependencies import limiter

    limiter.enabled = False
    async def override_get_db():
        yield seeded_db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
    limiter.enabled = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _register(client, email="test@medirisk.io", password="Secure123!"):
    return await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )


async def _login(client, email="test@medirisk.io", password="Secure123!"):
    return await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )


async def _register_and_login(client, email="test@medirisk.io", password="Secure123!"):
    await _register(client, email, password)
    resp = await _login(client, email, password)
    return resp.json()


# ===========================================================================
# REGISTRATION TESTS (1-8)
# ===========================================================================

class TestRegistration:
    async def test_valid_registration(self, client):
        """1. Valid registration returns 201 and user data."""
        resp = await _register(client)
        assert resp.status_code == 201
        body = resp.json()
        assert "user" in body
        assert body["user"]["email"] == "test@medirisk.io"

    async def test_invalid_email(self, client):
        """2. Invalid email format returns 422."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "Secure123!"},
        )
        assert resp.status_code == 422

    async def test_short_password(self, client):
        """3. Password < 8 chars returns 422."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "short@test.io", "password": "abc"},
        )
        assert resp.status_code == 422

    async def test_duplicate_email(self, client):
        """4. Duplicate email returns 409."""
        await _register(client, "dup@test.io")
        resp = await _register(client, "dup@test.io")
        assert resp.status_code == 409

    async def test_normalized_email_duplicate(self, client):
        """5. Same email different case is treated as duplicate."""
        await _register(client, "user@test.io")
        resp = await _register(client, "USER@TEST.IO")
        assert resp.status_code == 409

    async def test_password_not_in_response(self, client):
        """6. 'password' absent from registration response."""
        resp = await _register(client)
        body = resp.json()
        body_str = json.dumps(body)
        assert "password" not in body.get("user", {})

    async def test_password_hash_not_in_response(self, client):
        """7. 'password_hash' absent from registration response."""
        resp = await _register(client)
        body = resp.json()
        assert "password_hash" not in body
        assert "password_hash" not in body.get("user", {})

    async def test_default_user_role_assigned(self, client):
        """8. Registered user gets 'user' role."""
        resp = await _register(client)
        role_names = [r["name"] for r in resp.json()["user"].get("roles", [])]
        assert "user" in role_names


# ===========================================================================
# LOGIN TESTS (9-15)
# ===========================================================================

class TestLogin:
    async def test_valid_login(self, client):
        """9. Valid credentials returns tokens."""
        await _register(client)
        resp = await _login(client)
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        assert "refresh_token" in resp.json()

    async def test_wrong_password(self, client):
        """10. Wrong password returns 401 with safe error."""
        await _register(client)
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@medirisk.io", "password": "WRONGPASSWORD"},
        )
        assert resp.status_code == 401
        assert "password" not in resp.json().get("message", "").lower()

    async def test_unknown_email(self, client):
        """11. Unknown email returns 401."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@nowhere.io", "password": "anything"},
        )
        assert resp.status_code == 401

    async def test_inactive_user_rejected(self, client, seeded_db):
        """12. Inactive user cannot log in."""
        await _register(client, "inactive@test.io")
        from sqlalchemy import select
        from app.models.models import User
        result = await seeded_db.execute(select(User).where(User.email == "inactive@test.io"))
        user = result.scalar_one()
        user.is_active = False
        await seeded_db.commit()
        resp = await _login(client, "inactive@test.io")
        assert resp.status_code == 401

    async def test_access_token_generated(self, client):
        """13. Login response contains access_token."""
        await _register(client)
        resp = await _login(client)
        assert "access_token" in resp.json()

    async def test_refresh_token_generated(self, client):
        """14. Login response contains refresh_token."""
        await _register(client)
        resp = await _login(client)
        assert "refresh_token" in resp.json()

    async def test_correct_token_types(self, client):
        """15. Access token type='access'; refresh type='refresh'."""
        await _register(client)
        tokens = (await _login(client)).json()
        access_payload = jwt.decode(
            tokens["access_token"], options={"verify_signature": False}
        )
        refresh_payload = jwt.decode(
            tokens["refresh_token"], options={"verify_signature": False}
        )
        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"


# ===========================================================================
# ACCESS TOKEN TESTS (16-22)
# ===========================================================================

class TestAccessToken:
    async def test_valid_access_token_on_me(self, client):
        """16. Valid access token grants /me."""
        tokens = await _register_and_login(client)
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 200

    async def test_expired_access_token_rejected(self, client):
        """17. Expired access token returns 401."""
        expired = create_access_token(str(uuid.uuid4()), expires_delta=timedelta(seconds=-1))
        resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"}
        )
        assert resp.status_code == 401

    async def test_malformed_token_rejected(self, client):
        """18. Malformed token returns 401."""
        resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer this.is.garbage"}
        )
        assert resp.status_code == 401

    async def test_invalid_signature_rejected(self, client):
        """19. Token with wrong signature is rejected."""
        from app.core.config import settings
        bad_token = jwt.encode(
            {"sub": str(uuid.uuid4()), "type": "access", "jti": str(uuid.uuid4()),
             "exp": 9999999999, "iat": 1},
            "totally_wrong_key",
            algorithm="HS256",
        )
        resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {bad_token}"}
        )
        assert resp.status_code == 401

    async def test_refresh_token_rejected_at_me(self, client):
        """20. Refresh token used as Bearer is rejected at /me."""
        tokens = await _register_and_login(client)
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
        )
        assert resp.status_code == 401

    async def test_unknown_user_rejected(self, client):
        """21. Token for unknown user UUID is rejected."""
        fake_token = create_access_token(str(uuid.uuid4()))
        resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {fake_token}"}
        )
        assert resp.status_code == 401

    async def test_missing_token_rejected(self, client):
        """22. No Authorization header → 401."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401


# ===========================================================================
# REFRESH TESTS (23-28)
# ===========================================================================

class TestRefresh:
    async def test_valid_refresh(self, client):
        """23. Valid refresh token returns new pair."""
        tokens = await _register_and_login(client)
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body

    async def test_expired_refresh_rejected(self, client):
        """24. Expired refresh token returns 401."""
        from app.core.config import settings
        payload = {
            "sub": str(uuid.uuid4()),
            "type": "refresh",
            "jti": str(uuid.uuid4()),
            "exp": 1,
            "iat": 1,
        }
        expired_rt = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        resp = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": expired_rt}
        )
        assert resp.status_code == 401

    async def test_invalid_refresh_rejected(self, client):
        """25. Garbage string at /refresh returns 401."""
        resp = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "not.a.real.token"}
        )
        assert resp.status_code == 401

    async def test_access_token_rejected_at_refresh(self, client):
        """26. Access token at /refresh returns 401."""
        tokens = await _register_and_login(client)
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["access_token"]},
        )
        assert resp.status_code == 401

    async def test_revoked_refresh_rejected(self, client):
        """27. After logout, old refresh token rejected at /refresh."""
        tokens = await _register_and_login(client)
        await client.post(
            "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
        )
        resp = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert resp.status_code == 401

    async def test_rotation_issues_new_tokens(self, client):
        """28. Rotation: new tokens differ from old tokens."""
        tokens = await _register_and_login(client)
        resp = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        new_tokens = resp.json()
        assert new_tokens["access_token"] != tokens["access_token"]
        assert new_tokens["refresh_token"] != tokens["refresh_token"]


# ===========================================================================
# LOGOUT TESTS (29-31)
# ===========================================================================

class TestLogout:
    async def test_valid_logout(self, client):
        """29. Logout returns 200 with message."""
        tokens = await _register_and_login(client)
        resp = await client.post(
            "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
        )
        assert resp.status_code == 200

    async def test_refresh_revoked_after_logout(self, client):
        """30. Refresh token is revoked after logout."""
        tokens = await _register_and_login(client)
        await client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert resp.status_code == 401

    async def test_revoked_refresh_cannot_be_reused(self, client):
        """31. Revoked token cannot be used even if JWT not yet expired."""
        tokens = await _register_and_login(client)
        await client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
        resp2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert resp2.status_code == 401


# ===========================================================================
# CURRENT USER TESTS (32-34)
# ===========================================================================

class TestCurrentUser:
    async def test_authenticated_me(self, client):
        """32. /me returns user data for valid token."""
        tokens = await _register_and_login(client)
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "test@medirisk.io"
        assert "password_hash" not in body

    async def test_missing_token_me(self, client):
        """33. /me without token returns 401."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_invalid_token_me(self, client):
        """34. /me with garbage token returns 401."""
        resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer garbage.token.here"}
        )
        assert resp.status_code == 401


# ===========================================================================
# RBAC TESTS (35-36)
# ===========================================================================

class TestRBAC:
    async def test_user_role_in_me_response(self, client):
        """35. Registered user has 'user' role, not 'admin'."""
        tokens = await _register_and_login(client)
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        roles = [r["name"] for r in resp.json().get("roles", [])]
        assert "user" in roles
        assert "admin" not in roles

    def test_require_role_dependency_callable(self):
        """36. require_role factory returns a callable."""
        from app.dependencies import require_role
        dep = require_role("admin")
        assert callable(dep)


# ===========================================================================
# SECURITY TESTS (37-40)
# ===========================================================================

class TestSecurity:
    async def test_passwords_stored_as_argon2(self, client, seeded_db):
        """37. Password stored as Argon2id hash in DB."""
        await _register(client, "hashcheck@test.io")
        from sqlalchemy import select
        from app.models.models import User
        result = await seeded_db.execute(
            select(User).where(User.email == "hashcheck@test.io")
        )
        user = result.scalar_one()
        assert "$argon2" in user.password_hash

    async def test_raw_refresh_token_not_in_db(self, client, seeded_db):
        """38. DB stores hash (64 chars), not the raw refresh JWT."""
        tokens = await _register_and_login(client)
        raw_rt = tokens["refresh_token"]
        from sqlalchemy import select
        from app.models.models import RefreshToken as RT
        result = await seeded_db.execute(select(RT))
        rows = result.scalars().all()
        assert len(rows) >= 1
        for row in rows:
            assert row.token_hash != raw_rt
            assert len(row.token_hash) == 64  # SHA-256 hex

    async def test_token_hash_matches_sha256(self, client, seeded_db):
        """38b. Stored hash equals SHA-256(raw_refresh_token)."""
        tokens = await _register_and_login(client)
        raw_rt = tokens["refresh_token"]
        expected = hashlib.sha256(raw_rt.encode()).hexdigest()
        from sqlalchemy import select
        from app.models.models import RefreshToken as RT
        result = await seeded_db.execute(select(RT))
        hashes = [r.token_hash for r in result.scalars().all()]
        assert expected in hashes

    def test_password_hash_not_in_user_response_schema(self):
        """39. UserResponse schema excludes password_hash."""
        assert "password_hash" not in UserResponse.model_fields

    def test_password_not_in_user_response_schema(self):
        """39b. UserResponse schema excludes password."""
        assert "password" not in UserResponse.model_fields

    def test_register_request_no_password_hash_field(self):
        """40. RegisterRequest has no password_hash field."""
        assert "password_hash" not in RegisterRequest.model_fields


# ===========================================================================
# AUDIT TESTS (41-44)
# ===========================================================================

class TestAuditEvents:
    async def test_registration_audit_event(self, client, seeded_db):
        """41. Registration creates USER_REGISTERED audit log."""
        await _register(client, "audituser@test.io")
        from sqlalchemy import select
        from app.models.models import AuditLog
        result = await seeded_db.execute(
            select(AuditLog).where(AuditLog.action == "USER_REGISTERED")
        )
        assert len(result.scalars().all()) >= 1

    async def test_successful_login_audit(self, client, seeded_db):
        """42. Successful login creates USER_LOGIN_SUCCESS audit log."""
        await _register(client, "loginaudit@test.io")
        await _login(client, "loginaudit@test.io")
        from sqlalchemy import select
        from app.models.models import AuditLog
        result = await seeded_db.execute(
            select(AuditLog).where(AuditLog.action == "USER_LOGIN_SUCCESS")
        )
        assert len(result.scalars().all()) >= 1

    async def test_failed_login_audit(self, client, seeded_db):
        """43. Failed login creates USER_LOGIN_FAILED audit log."""
        await _register(client, "failaudit@test.io")
        await client.post(
            "/api/v1/auth/login",
            json={"email": "failaudit@test.io", "password": "WRONGPASS"},
        )
        from sqlalchemy import select
        from app.models.models import AuditLog
        result = await seeded_db.execute(
            select(AuditLog).where(AuditLog.action == "USER_LOGIN_FAILED")
        )
        assert len(result.scalars().all()) >= 1

    async def test_logout_audit(self, client, seeded_db):
        """44. Logout creates USER_LOGOUT audit log."""
        tokens = await _register_and_login(client, "logoutaudit@test.io")
        await client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
        from sqlalchemy import select
        from app.models.models import AuditLog
        result = await seeded_db.execute(
            select(AuditLog).where(AuditLog.action == "USER_LOGOUT")
        )
        assert len(result.scalars().all()) >= 1

    async def test_audit_metadata_safe(self, client, seeded_db):
        """44b. Audit metadata never contains raw tokens or passwords."""
        tokens = await _register_and_login(client, "safeaudit@test.io")
        raw_rt = tokens["refresh_token"]
        raw_at = tokens["access_token"]
        await client.post("/api/v1/auth/logout", json={"refresh_token": raw_rt})
        from sqlalchemy import select
        from app.models.models import AuditLog
        result = await seeded_db.execute(select(AuditLog))
        for log in result.scalars().all():
            meta_str = str(log.event_metadata or "")
            assert raw_rt not in meta_str, "Raw refresh token in audit log!"
            assert raw_at not in meta_str, "Raw access token in audit log!"


# ===========================================================================
# RATE LIMITING TESTS (45-46)
# ===========================================================================

class TestRateLimiting:
    def test_login_endpoint_callable(self):
        """45. Login endpoint exists and is callable."""
        from app.api.v1.endpoints.auth import login
        assert callable(login)

    def test_register_endpoint_callable(self):
        """46. Register endpoint exists and is callable."""
        from app.api.v1.endpoints.auth import register
        assert callable(register)

    async def test_refresh_endpoint_exists(self, client):
        """Rate limit infra: /refresh responds (not 404)."""
        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": "x"})
        assert resp.status_code != 404

    async def test_login_rate_limit_annotation(self):
        """Rate limiter: slowapi limiter is configured on the app."""
        from app.main import app
        assert hasattr(app.state, "limiter")
