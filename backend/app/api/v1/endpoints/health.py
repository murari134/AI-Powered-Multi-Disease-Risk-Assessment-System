"""
MediRisk 2.0 — Health Endpoints
Phase 4: Backend Core

GET /api/v1/health        — liveness
GET /api/v1/health/ready  — readiness (PostgreSQL + Redis)
"""

import logging
import time

from fastapi import APIRouter, Request
from sqlalchemy import text

from app.core.redis_client import ping_redis
from app.core.config import settings
from app.db.session import engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="Liveness check")
async def liveness(request: Request):
    """
    Returns OK when the application process is running.
    Does not check downstream dependencies.
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "request_id": getattr(request.state, "request_id", "-"),
    }


@router.get("/ready", summary="Readiness check")
async def readiness(request: Request):
    """
    Returns the health of all downstream dependencies.
    Returns HTTP 200 when all are healthy, HTTP 503 when any are unavailable.
    PostgreSQL live check is deferred until Docker is available in this environment.
    """
    checks: dict = {}
    overall_healthy = True

    # ------------------------------------------------------------------
    # PostgreSQL
    # ------------------------------------------------------------------
    pg_start = time.monotonic()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgresql"] = {
            "status": "ok",
            "latency_ms": round((time.monotonic() - pg_start) * 1000, 2),
        }
    except Exception as exc:
        overall_healthy = False
        checks["postgresql"] = {
            "status": "unavailable",
            "detail": "PostgreSQL is not reachable. "
            "Start Docker Compose to enable live validation.",
        }
        logger.warning("PostgreSQL readiness check failed: %s", exc)

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    redis_start = time.monotonic()
    redis_ok = await ping_redis()
    if redis_ok:
        checks["redis"] = {
            "status": "ok",
            "latency_ms": round((time.monotonic() - redis_start) * 1000, 2),
        }
    else:
        overall_healthy = False
        checks["redis"] = {
            "status": "unavailable",
            "detail": "Redis is not reachable.",
        }

    status_code = 200 if overall_healthy else 503
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if overall_healthy else "degraded",
            "checks": checks,
            "request_id": getattr(request.state, "request_id", "-"),
        },
    )
