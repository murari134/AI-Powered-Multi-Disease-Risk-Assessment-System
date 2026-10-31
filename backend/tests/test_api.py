"""
MediRisk 2.0 — Phase 4 API Tests
Tests: /health, /api/v1/health, readiness, request ID, CORS, error format.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


# ---------------------------------------------------------------------------
# Async test client fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# 1. Root health check
# ---------------------------------------------------------------------------

class TestRootHealth:
    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_health_returns_ok_status(self, client):
        resp = await client.get("/health")
        body = resp.json()
        assert body["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_returns_app_name(self, client):
        resp = await client.get("/health")
        body = resp.json()
        assert "app" in body

    @pytest.mark.asyncio
    async def test_health_returns_version(self, client):
        resp = await client.get("/health")
        body = resp.json()
        assert "version" in body


# ---------------------------------------------------------------------------
# 2. /api/v1/health liveness
# ---------------------------------------------------------------------------

class TestV1Health:
    @pytest.mark.asyncio
    async def test_v1_health_returns_200(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_v1_health_returns_ok_status(self, client):
        resp = await client.get("/api/v1/health")
        body = resp.json()
        assert body["status"] == "ok"

    @pytest.mark.asyncio
    async def test_v1_health_contains_request_id(self, client):
        resp = await client.get("/api/v1/health")
        body = resp.json()
        assert "request_id" in body


# ---------------------------------------------------------------------------
# 3. Readiness endpoint
# ---------------------------------------------------------------------------

class TestReadiness:
    @pytest.mark.asyncio
    async def test_readiness_endpoint_responds(self, client):
        """Readiness endpoint must respond (200 or 503 depending on DB/Redis)."""
        resp = await client.get("/api/v1/health/ready")
        assert resp.status_code in (200, 503)

    @pytest.mark.asyncio
    async def test_readiness_body_has_status_field(self, client):
        resp = await client.get("/api/v1/health/ready")
        body = resp.json()
        assert "status" in body
        assert body["status"] in ("ready", "degraded")

    @pytest.mark.asyncio
    async def test_readiness_body_has_checks(self, client):
        resp = await client.get("/api/v1/health/ready")
        body = resp.json()
        assert "checks" in body
        assert "postgresql" in body["checks"]
        assert "redis" in body["checks"]

    @pytest.mark.asyncio
    async def test_readiness_returns_503_when_db_offline(self, client):
        """
        Without Docker running, PostgreSQL is unavailable.
        Readiness must return 503 (not fake a 200).
        """
        resp = await client.get("/api/v1/health/ready")
        # In CI/dev without Docker this must be 503
        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["checks"]["postgresql"]["status"] == "unavailable"


# ---------------------------------------------------------------------------
# 4. Request ID generation & propagation
# ---------------------------------------------------------------------------

class TestRequestID:
    @pytest.mark.asyncio
    async def test_request_id_in_response_header(self, client):
        resp = await client.get("/health")
        assert "x-request-id" in resp.headers

    @pytest.mark.asyncio
    async def test_request_id_is_non_empty(self, client):
        resp = await client.get("/health")
        assert len(resp.headers.get("x-request-id", "")) > 0

    @pytest.mark.asyncio
    async def test_client_request_id_propagated(self, client):
        custom_id = "test-correlation-abc-123"
        resp = await client.get("/health", headers={"X-Request-ID": custom_id})
        assert resp.headers.get("x-request-id") == custom_id

    @pytest.mark.asyncio
    async def test_request_id_in_health_body(self, client):
        resp = await client.get("/api/v1/health")
        body = resp.json()
        header_id = resp.headers.get("x-request-id")
        assert body["request_id"] == header_id

    @pytest.mark.asyncio
    async def test_each_request_gets_unique_id(self, client):
        ids = set()
        for _ in range(5):
            resp = await client.get("/health")
            ids.add(resp.headers.get("x-request-id"))
        assert len(ids) == 5


# ---------------------------------------------------------------------------
# 5. Error response format
# ---------------------------------------------------------------------------

class TestErrorResponseFormat:
    @pytest.mark.asyncio
    async def test_404_returns_json(self, client):
        resp = await client.get("/this-route-does-not-exist")
        # FastAPI default 404 is JSON
        assert resp.headers.get("content-type", "").startswith("application/json")

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, client):
        resp = await client.post("/health")
        assert resp.status_code == 405

    @pytest.mark.asyncio
    async def test_invalid_path_gives_non_200(self, client):
        resp = await client.get("/api/v1/does-not-exist-at-all")
        assert resp.status_code >= 400


# ---------------------------------------------------------------------------
# 6. CORS configuration
# ---------------------------------------------------------------------------

class TestCORS:
    @pytest.mark.asyncio
    async def test_cors_allowed_origin_reflected(self, client):
        resp = await client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"

    @pytest.mark.asyncio
    async def test_cors_disallowed_origin_not_reflected(self, client):
        resp = await client.get(
            "/health",
            headers={"Origin": "http://evil-site.example"},
        )
        # Disallowed origin — header should not echo it back
        allow = resp.headers.get("access-control-allow-origin", "")
        assert allow != "http://evil-site.example"
