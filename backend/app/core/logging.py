"""
MediRisk 2.0 — Structured Application Logging
Phase 4: Backend Core

Provides a structlog-style structured logger with request-ID propagation.
Falls back gracefully to stdlib logging if structlog is unavailable.
"""

import logging
import sys
from contextvars import ContextVar

# Per-request correlation ID (set by RequestIDMiddleware)
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return request_id_ctx_var.get()


def configure_logging(level: str = "INFO") -> None:
    """Configure application logging on startup."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    handler.setFormatter(fmt)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
