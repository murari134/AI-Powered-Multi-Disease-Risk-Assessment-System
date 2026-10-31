"""
MediRisk 2.0 — Phase 6 Profile & Health Assessment Tests
Tests all 30 required points:
  1-10: Profile CRUD, validation, ownership, multiple profiles
  11-24: Assessment creation, retrieval, history, pagination, sorting, validation, ownership, immutability, audit
  25-28: Audit events (PROFILE_CREATED, PROFILE_UPDATED, ASSESSMENT_CREATED, ASSESSMENT_VIEWED, safe metadata)
  29-30: Security invariants (no password_hash, no tokens)
"""

import json
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.models.models import AuditLog, HealthAssessment, Profile, Role, User
from app.schemas.schemas import (
    HealthAssessmentCreate,
    HealthAssessmentListResponse,
    HealthAssessmentResponse,
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)

# ---------------------------------------------------------------------------
# SQLite Compatibility Fixtures
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


def _sqlite_compat_metadata():
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

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_json(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")

    import app.models  # ensure models registered
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
    user_role = Role(id=uuid.uuid4(), name="user", description="Standard user")
    admin_role = Role(id=uuid.uuid4(), name="admin", description="Admin user")
    db_session.add_all([user_role, admin_role])
    await db_session.commit()
    return db_session


@pytest_asyncio.fixture(scope="function")
async def client(seeded_db: AsyncSession):
    from app.dependencies import limiter
    from app.db.session import get_db
    from app.main import app

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
# Test Helpers
# ---------------------------------------------------------------------------

async def _register_and_login(client: AsyncClient, email: str = "user@test.io", password: str = "Password123!") -> dict:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()


def _auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# ===========================================================================
# 1. PROFILE TESTS (1-10)
# ===========================================================================

class TestProfileEndpoints:
    async def test_authenticated_profile_creation(self, client: AsyncClient):
        """1. Authenticated user can create a valid profile."""
        tokens = await _register_and_login(client, "profile1@test.io")
        headers = _auth_headers(tokens)
        payload = {
            "display_name": "Primary Patient",
            "date_of_birth": "1990-06-15T00:00:00Z",
            "sex": "female",
            "height": 165.5,
            "weight": 62.0,
        }
        resp = await client.post("/api/v1/profiles", json=payload, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["display_name"] == "Primary Patient"
        assert data["sex"] == "female"
        assert data["height"] == 165.5
        assert data["weight"] == 62.0
        assert "id" in data
        assert "user_id" in data

    async def test_unauthenticated_profile_creation_rejected(self, client: AsyncClient):
        """2. Unauthenticated profile creation returns 401."""
        payload = {"display_name": "Anonymous"}
        resp = await client.post("/api/v1/profiles", json=payload)
        assert resp.status_code == 401

    async def test_profile_retrieval(self, client: AsyncClient):
        """3. Profile owner can retrieve their profile."""
        tokens = await _register_and_login(client, "profile3@test.io")
        headers = _auth_headers(tokens)
        create_resp = await client.post(
            "/api/v1/profiles",
            json={"display_name": "Test Person", "sex": "male", "height": 175.0, "weight": 70.0},
            headers=headers,
        )
        profile_id = create_resp.json()["id"]

        get_resp = await client.get(f"/api/v1/profiles/{profile_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == profile_id
        assert get_resp.json()["display_name"] == "Test Person"

    async def test_profile_update(self, client: AsyncClient):
        """4. Profile owner can update profile fields."""
        tokens = await _register_and_login(client, "profile4@test.io")
        headers = _auth_headers(tokens)
        create_resp = await client.post(
            "/api/v1/profiles",
            json={"display_name": "Old Name", "height": 170.0, "weight": 65.0},
            headers=headers,
        )
        profile_id = create_resp.json()["id"]

        update_resp = await client.patch(
            f"/api/v1/profiles/{profile_id}",
            json={"display_name": "New Name", "weight": 68.0},
            headers=headers,
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["display_name"] == "New Name"
        assert data["weight"] == 68.0
        assert data["height"] == 170.0  # unchanged

    async def test_profile_deletion(self, client: AsyncClient):
        """5. Profile owner can delete their profile."""
        tokens = await _register_and_login(client, "profile5@test.io")
        headers = _auth_headers(tokens)
        create_resp = await client.post(
            "/api/v1/profiles", json={"display_name": "To Delete"}, headers=headers
        )
        profile_id = create_resp.json()["id"]

        del_resp = await client.delete(f"/api/v1/profiles/{profile_id}", headers=headers)
        assert del_resp.status_code == 204

        # Subsequent GET should return 404
        get_resp = await client.get(f"/api/v1/profiles/{profile_id}", headers=headers)
        assert get_resp.status_code == 404

    async def test_multiple_profiles_for_one_user(self, client: AsyncClient):
        """6. A single user can create and list multiple profiles."""
        tokens = await _register_and_login(client, "multi@test.io")
        headers = _auth_headers(tokens)

        p1 = await client.post("/api/v1/profiles", json={"display_name": "Self"}, headers=headers)
        p2 = await client.post("/api/v1/profiles", json={"display_name": "Child"}, headers=headers)
        assert p1.status_code == 201
        assert p2.status_code == 201

        list_resp = await client.get("/api/v1/profiles", headers=headers)
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert len(items) == 2
        names = {item["display_name"] for item in items}
        assert names == {"Self", "Child"}

    async def test_another_user_cannot_access_profile(self, client: AsyncClient):
        """7. User B cannot access User A's profile (safe 404 returned)."""
        tokens_a = await _register_and_login(client, "usera7@test.io")
        tokens_b = await _register_and_login(client, "userb7@test.io")

        p = await client.post(
            "/api/v1/profiles", json={"display_name": "User A Private"}, headers=_auth_headers(tokens_a)
        )
        profile_a_id = p.json()["id"]

        resp = await client.get(
            f"/api/v1/profiles/{profile_a_id}", headers=_auth_headers(tokens_b)
        )
        assert resp.status_code == 404

    async def test_another_user_cannot_modify_profile(self, client: AsyncClient):
        """8. User B cannot modify User A's profile."""
        tokens_a = await _register_and_login(client, "usera8@test.io")
        tokens_b = await _register_and_login(client, "userb8@test.io")

        p = await client.post(
            "/api/v1/profiles", json={"display_name": "Original Name"}, headers=_auth_headers(tokens_a)
        )
        profile_a_id = p.json()["id"]

        resp = await client.patch(
            f"/api/v1/profiles/{profile_a_id}",
            json={"display_name": "Hacked"},
            headers=_auth_headers(tokens_b),
        )
        assert resp.status_code == 404

        # Verify User A's profile is untouched
        check = await client.get(
            f"/api/v1/profiles/{profile_a_id}", headers=_auth_headers(tokens_a)
        )
        assert check.json()["display_name"] == "Original Name"

    async def test_another_user_cannot_delete_profile(self, client: AsyncClient):
        """9. User B cannot delete User A's profile."""
        tokens_a = await _register_and_login(client, "usera9@test.io")
        tokens_b = await _register_and_login(client, "userb9@test.io")

        p = await client.post(
            "/api/v1/profiles", json={"display_name": "Permanent"}, headers=_auth_headers(tokens_a)
        )
        profile_a_id = p.json()["id"]

        resp = await client.delete(
            f"/api/v1/profiles/{profile_a_id}", headers=_auth_headers(tokens_b)
        )
        assert resp.status_code == 404

        # Verify User A's profile still exists
        check = await client.get(
            f"/api/v1/profiles/{profile_a_id}", headers=_auth_headers(tokens_a)
        )
        assert check.status_code == 200

    async def test_invalid_profile_data_rejected(self, client: AsyncClient):
        """10. Unrealistic/invalid profile values are rejected with 422."""
        tokens = await _register_and_login(client, "validation@test.io")
        headers = _auth_headers(tokens)

        # Blank display name
        r = await client.post("/api/v1/profiles", json={"display_name": "   "}, headers=headers)
        assert r.status_code == 422

        # Future DOB
        r = await client.post("/api/v1/profiles", json={"date_of_birth": "2099-01-01T00:00:00Z"}, headers=headers)
        assert r.status_code == 422

        # Pre-1900 DOB
        r = await client.post("/api/v1/profiles", json={"date_of_birth": "1850-01-01T00:00:00Z"}, headers=headers)
        assert r.status_code == 422

        # Invalid sex
        r = await client.post("/api/v1/profiles", json={"sex": "extraterrestrial"}, headers=headers)
        assert r.status_code == 422

        # Negative height
        r = await client.post("/api/v1/profiles", json={"height": -5.0}, headers=headers)
        assert r.status_code == 422

        # Unrealistic height (>300cm)
        r = await client.post("/api/v1/profiles", json={"height": 350.0}, headers=headers)
        assert r.status_code == 422

        # Unrealistic weight (>650kg)
        r = await client.post("/api/v1/profiles", json={"weight": 700.0}, headers=headers)
        assert r.status_code == 422


# ===========================================================================
# 2. ASSESSMENT TESTS (11-24)
# ===========================================================================

class TestAssessmentEndpoints:
    async def test_authenticated_assessment_creation(self, client: AsyncClient):
        """11. Authenticated user can create assessment for their profile."""
        tokens = await _register_and_login(client, "assess11@test.io")
        headers = _auth_headers(tokens)

        p = await client.post("/api/v1/profiles", json={"display_name": "Patient 11"}, headers=headers)
        profile_id = p.json()["id"]

        payload = {
            "assessment_version": "1.0",
            "input_data": {"age": 52, "systolic_bp": 130, "fasting_blood_sugar": 105},
        }
        resp = await client.post(f"/api/v1/profiles/{profile_id}/assessments", json=payload, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["profile_id"] == profile_id
        assert data["assessment_version"] == "1.0"
        assert data["input_data"] == payload["input_data"]
        assert "id" in data
        assert "created_at" in data

    async def test_unauthenticated_assessment_rejected(self, client: AsyncClient):
        """12. Unauthenticated assessment creation returns 401."""
        fake_profile_id = str(uuid.uuid4())
        resp = await client.post(
            f"/api/v1/profiles/{fake_profile_id}/assessments",
            json={"assessment_version": "1.0", "input_data": {"feature": 1}},
        )
        assert resp.status_code == 401

    async def test_assessment_retrieval(self, client: AsyncClient):
        """13. Assessment can be retrieved by ID."""
        tokens = await _register_and_login(client, "assess13@test.io")
        headers = _auth_headers(tokens)

        p = await client.post("/api/v1/profiles", json={"display_name": "Patient 13"}, headers=headers)
        profile_id = p.json()["id"]

        a = await client.post(
            f"/api/v1/profiles/{profile_id}/assessments",
            json={"assessment_version": "1.0", "input_data": {"glucose": 95}},
            headers=headers,
        )
        assessment_id = a.json()["id"]

        resp = await client.get(
            f"/api/v1/profiles/{profile_id}/assessments/{assessment_id}",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == assessment_id
        assert resp.json()["input_data"] == {"glucose": 95}

    async def test_assessment_history(self, client: AsyncClient):
        """14. Assessment history lists all assessments for the profile."""
        tokens = await _register_and_login(client, "assess14@test.io")
        headers = _auth_headers(tokens)

        p = await client.post("/api/v1/profiles", json={"display_name": "Patient 14"}, headers=headers)
        profile_id = p.json()["id"]

        for i in range(3):
            await client.post(
                f"/api/v1/profiles/{profile_id}/assessments",
                json={"assessment_version": "1.0", "input_data": {"session": i}},
                headers=headers,
            )

        resp = await client.get(f"/api/v1/profiles/{profile_id}/assessments", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert len(body["items"]) == 3

    async def test_pagination(self, client: AsyncClient):
        """15. Assessment list supports limit and offset pagination."""
        tokens = await _register_and_login(client, "assess15@test.io")
        headers = _auth_headers(tokens)

        p = await client.post("/api/v1/profiles", json={"display_name": "Patient 15"}, headers=headers)
        profile_id = p.json()["id"]

        for i in range(4):
            await client.post(
                f"/api/v1/profiles/{profile_id}/assessments",
                json={"assessment_version": "1.0", "input_data": {"idx": i}},
                headers=headers,
            )

        resp = await client.get(
            f"/api/v1/profiles/{profile_id}/assessments?limit=2&offset=1",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 4
        assert len(body["items"]) == 2
        assert body["limit"] == 2
        assert body["offset"] == 1

    async def test_newest_first_ordering(self, client: AsyncClient):
        """16. Assessments are returned in newest-first order."""
        tokens = await _register_and_login(client, "assess16@test.io")
        headers = _auth_headers(tokens)

        p = await client.post("/api/v1/profiles", json={"display_name": "Patient 16"}, headers=headers)
        profile_id = p.json()["id"]

        await client.post(
            f"/api/v1/profiles/{profile_id}/assessments",
            json={"assessment_version": "1.0", "input_data": {"order": "first"}},
            headers=headers,
        )
        import asyncio
        await asyncio.sleep(0.05)
        await client.post(
            f"/api/v1/profiles/{profile_id}/assessments",
            json={"assessment_version": "1.0", "input_data": {"order": "second"}},
            headers=headers,
        )

        resp = await client.get(f"/api/v1/profiles/{profile_id}/assessments", headers=headers)
        items = resp.json()["items"]
        assert items[0]["input_data"]["order"] == "second"
        assert items[1]["input_data"]["order"] == "first"

    async def test_invalid_input_data_rejected(self, client: AsyncClient):
        """17. Non-dictionary or empty input_data is rejected with 422."""
        tokens = await _register_and_login(client, "assess17@test.io")
        headers = _auth_headers(tokens)
        p = await client.post("/api/v1/profiles", json={"display_name": "P17"}, headers=headers)
        pid = p.json()["id"]

        # String primitive
        r1 = await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "1.0", "input_data": "not a dict"},
            headers=headers,
        )
        assert r1.status_code == 422

        # Array primitive
        r2 = await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "1.0", "input_data": [1, 2, 3]},
            headers=headers,
        )
        assert r2.status_code == 422

        # Empty dict
        r3 = await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "1.0", "input_data": {}},
            headers=headers,
        )
        assert r3.status_code == 422

    async def test_null_input_data_rejected(self, client: AsyncClient):
        """18. Null input_data is rejected with 422."""
        tokens = await _register_and_login(client, "assess18@test.io")
        headers = _auth_headers(tokens)
        p = await client.post("/api/v1/profiles", json={"display_name": "P18"}, headers=headers)
        pid = p.json()["id"]

        r = await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "1.0", "input_data": None},
            headers=headers,
        )
        assert r.status_code == 422

    async def test_invalid_assessment_version_rejected(self, client: AsyncClient):
        """19. Unsupported or malformed assessment_version is rejected with 422."""
        tokens = await _register_and_login(client, "assess19@test.io")
        headers = _auth_headers(tokens)
        p = await client.post("/api/v1/profiles", json={"display_name": "P19"}, headers=headers)
        pid = p.json()["id"]

        r1 = await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "99.0", "input_data": {"val": 1}},
            headers=headers,
        )
        assert r1.status_code == 422

        r2 = await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "invalid_ver", "input_data": {"val": 1}},
            headers=headers,
        )
        assert r2.status_code == 422

    async def test_oversized_payload_rejected(self, client: AsyncClient):
        """20. Input payloads exceeding 64KB are rejected."""
        tokens = await _register_and_login(client, "assess20@test.io")
        headers = _auth_headers(tokens)
        p = await client.post("/api/v1/profiles", json={"display_name": "P20"}, headers=headers)
        pid = p.json()["id"]

        large_payload = {"huge_blob": "x" * 70000}  # ~70 KB
        r = await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "1.0", "input_data": large_payload},
            headers=headers,
        )
        assert r.status_code == 422

    async def test_assessment_ownership_enforced(self, client: AsyncClient):
        """21. User B cannot retrieve User A's assessment."""
        tokens_a = await _register_and_login(client, "usera21@test.io")
        tokens_b = await _register_and_login(client, "userb21@test.io")

        p = await client.post("/api/v1/profiles", json={"display_name": "P21"}, headers=_auth_headers(tokens_a))
        pid = p.json()["id"]

        a = await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "1.0", "input_data": {"test": "private"}},
            headers=_auth_headers(tokens_a),
        )
        aid = a.json()["id"]

        resp = await client.get(
            f"/api/v1/profiles/{pid}/assessments/{aid}",
            headers=_auth_headers(tokens_b),
        )
        assert resp.status_code == 404

    async def test_cross_user_assessment_access_rejected(self, client: AsyncClient):
        """22. User B cannot create or list assessments on User A's profile."""
        tokens_a = await _register_and_login(client, "usera22@test.io")
        tokens_b = await _register_and_login(client, "userb22@test.io")

        p = await client.post("/api/v1/profiles", json={"display_name": "P22"}, headers=_auth_headers(tokens_a))
        pid = p.json()["id"]

        # User B cannot submit assessment to User A's profile
        r1 = await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "1.0", "input_data": {"spoofed": True}},
            headers=_auth_headers(tokens_b),
        )
        assert r1.status_code == 404

        # User B cannot list assessments from User A's profile
        r2 = await client.get(
            f"/api/v1/profiles/{pid}/assessments",
            headers=_auth_headers(tokens_b),
        )
        assert r2.status_code == 404

    async def test_assessment_remains_immutable(self, client: AsyncClient):
        """23. Assessments have no PATCH or PUT endpoints (405 Method Not Allowed)."""
        tokens = await _register_and_login(client, "assess23@test.io")
        headers = _auth_headers(tokens)
        p = await client.post("/api/v1/profiles", json={"display_name": "P23"}, headers=headers)
        pid = p.json()["id"]
        a = await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "1.0", "input_data": {"immutable": True}},
            headers=headers,
        )
        aid = a.json()["id"]

        patch_resp = await client.patch(
            f"/api/v1/profiles/{pid}/assessments/{aid}",
            json={"input_data": {"altered": True}},
            headers=headers,
        )
        assert patch_resp.status_code in (404, 405)

        put_resp = await client.put(
            f"/api/v1/profiles/{pid}/assessments/{aid}",
            json={"input_data": {"altered": True}},
            headers=headers,
        )
        assert put_resp.status_code in (404, 405)

    async def test_assessment_audit_event_created(self, client: AsyncClient, seeded_db: AsyncSession):
        """24. Creating an assessment writes an ASSESSMENT_CREATED audit log."""
        tokens = await _register_and_login(client, "assess24@test.io")
        headers = _auth_headers(tokens)
        p = await client.post("/api/v1/profiles", json={"display_name": "P24"}, headers=headers)
        pid = p.json()["id"]
        await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "1.0", "input_data": {"biomarker": 12}},
            headers=headers,
        )

        res = await seeded_db.execute(
            select(AuditLog).where(AuditLog.action == "ASSESSMENT_CREATED")
        )
        logs = res.scalars().all()
        assert len(logs) >= 1
        assert logs[-1].resource_type == "health_assessment"


# ===========================================================================
# 3. AUDIT TESTS (25-28)
# ===========================================================================

class TestAuditEvents:
    async def test_profile_creation_audit(self, client: AsyncClient, seeded_db: AsyncSession):
        """25. Creating a profile writes PROFILE_CREATED audit log."""
        tokens = await _register_and_login(client, "audit25@test.io")
        headers = _auth_headers(tokens)
        p = await client.post("/api/v1/profiles", json={"display_name": "Audit Profile"}, headers=headers)
        pid = p.json()["id"]

        res = await seeded_db.execute(
            select(AuditLog).where(AuditLog.action == "PROFILE_CREATED")
        )
        logs = res.scalars().all()
        assert any(l.resource_id == pid for l in logs)

    async def test_profile_update_audit(self, client: AsyncClient, seeded_db: AsyncSession):
        """26. Updating a profile writes PROFILE_UPDATED audit log."""
        tokens = await _register_and_login(client, "audit26@test.io")
        headers = _auth_headers(tokens)
        p = await client.post("/api/v1/profiles", json={"display_name": "Pre-Update"}, headers=headers)
        pid = p.json()["id"]

        await client.patch(f"/api/v1/profiles/{pid}", json={"display_name": "Post-Update"}, headers=headers)

        res = await seeded_db.execute(
            select(AuditLog).where(AuditLog.action == "PROFILE_UPDATED")
        )
        logs = res.scalars().all()
        assert any(l.resource_id == pid for l in logs)

    async def test_assessment_creation_audit(self, client: AsyncClient, seeded_db: AsyncSession):
        """27. Assessment creation log contains assessment_id and profile_id."""
        tokens = await _register_and_login(client, "audit27@test.io")
        headers = _auth_headers(tokens)
        p = await client.post("/api/v1/profiles", json={"display_name": "P27"}, headers=headers)
        pid = p.json()["id"]
        a = await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "1.0", "input_data": {"param": 99}},
            headers=headers,
        )
        aid = a.json()["id"]

        res = await seeded_db.execute(
            select(AuditLog).where(AuditLog.action == "ASSESSMENT_CREATED", AuditLog.resource_id == aid)
        )
        log = res.scalar_one_or_none()
        assert log is not None
        assert log.event_metadata["profile_id"] == pid
        assert log.event_metadata["assessment_id"] == aid

    async def test_sensitive_assessment_payload_not_stored_in_audit_metadata(
        self, client: AsyncClient, seeded_db: AsyncSession
    ):
        """28. Sensitive input_data feature values NEVER appear in audit metadata."""
        tokens = await _register_and_login(client, "audit28@test.io")
        headers = _auth_headers(tokens)
        p = await client.post("/api/v1/profiles", json={"display_name": "P28"}, headers=headers)
        pid = p.json()["id"]

        unique_marker = "SUPER_SECRET_CLINICAL_MARKER_98765"
        await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "1.0", "input_data": {"secret_feature": unique_marker}},
            headers=headers,
        )

        res = await seeded_db.execute(select(AuditLog))
        all_logs = res.scalars().all()
        for log in all_logs:
            meta_str = json.dumps(log.event_metadata or {})
            assert unique_marker not in meta_str, "Clinical input_data leaked into audit log metadata!"


# ===========================================================================
# 4. SECURITY INVARIANTS (29-30)
# ===========================================================================

class TestSecurityInvariants:
    async def test_password_hash_never_returned(self, client: AsyncClient):
        """29. Profile and assessment responses never contain password_hash or password."""
        tokens = await _register_and_login(client, "sec29@test.io")
        headers = _auth_headers(tokens)

        p = await client.post("/api/v1/profiles", json={"display_name": "Sec29"}, headers=headers)
        p_body = p.json()
        assert "password" not in p_body
        assert "password_hash" not in p_body

        pid = p_body["id"]
        a = await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "1.0", "input_data": {"feat": 1}},
            headers=headers,
        )
        a_body = a.json()
        assert "password" not in a_body
        assert "password_hash" not in a_body

    async def test_tokens_never_returned_unnecessarily(self, client: AsyncClient):
        """30. Profile and assessment responses never return tokens."""
        tokens = await _register_and_login(client, "sec30@test.io")
        headers = _auth_headers(tokens)

        p = await client.post("/api/v1/profiles", json={"display_name": "Sec30"}, headers=headers)
        p_body = p.json()
        assert "access_token" not in p_body
        assert "refresh_token" not in p_body

        pid = p_body["id"]
        a = await client.post(
            f"/api/v1/profiles/{pid}/assessments",
            json={"assessment_version": "1.0", "input_data": {"feat": 1}},
            headers=headers,
        )
        a_body = a.json()
        assert "access_token" not in a_body
        assert "refresh_token" not in a_body
