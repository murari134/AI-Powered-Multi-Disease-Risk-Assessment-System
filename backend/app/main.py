"""
MediRisk 2.0 — FastAPI Application Entry Point
Phase 4: Backend Core
"""

import sys
from pathlib import Path

# Ensure venv site-packages and project root are in sys.path
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_VENV_SITE = _BACKEND_DIR / ".venv" / "Lib" / "site-packages"
_PROJECT_ROOT = _BACKEND_DIR.parent
if _VENV_SITE.exists() and str(_VENV_SITE) not in sys.path:
    sys.path.insert(0, str(_VENV_SITE))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.redis_client import close_redis
from app.dependencies import limiter
from app.middleware import LoggingMiddleware, RequestIDMiddleware

# ---------------------------------------------------------------------------
# Configure logging before anything else
# MediRisk 2.0 API routes reloaded
# ---------------------------------------------------------------------------
configure_logging(level="DEBUG" if settings.DEBUG else "INFO")
logger = logging.getLogger("medirisk.app")

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    description="MediRisk 2.0 — AI-Powered Multi-Disease Risk Assessment API",
    version=settings.APP_VERSION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# ---------------------------------------------------------------------------
# Rate limiting (slowapi)
# ---------------------------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ---------------------------------------------------------------------------
# CORS  — never allow_origins=["*"] when credentials=True
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ---------------------------------------------------------------------------
# Request ID + structured logging middleware
# ---------------------------------------------------------------------------
# NOTE: middleware stack is LIFO — RequestID runs first (outermost)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
register_exception_handlers(app)

# ---------------------------------------------------------------------------
# API v1 routes
# ---------------------------------------------------------------------------
app.include_router(api_v1_router)


# ---------------------------------------------------------------------------
# Root health check (liveness — no versioning required)
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"], summary="Root liveness check")
async def root_health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# ---------------------------------------------------------------------------
# Lifecycle events
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    logger.info(
        "MediRisk 2.0 API starting — env=%s version=%s",
        settings.ENVIRONMENT,
        settings.APP_VERSION,
    )


@app.on_event("shutdown")
async def on_shutdown():
    await close_redis()
    logger.info("MediRisk 2.0 API shutdown complete.")


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
    )
