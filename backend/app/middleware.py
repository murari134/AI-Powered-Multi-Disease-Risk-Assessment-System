"""
MediRisk 2.0 — Request ID & Logging Middleware
Phase 4: Backend Core

1. RequestIDMiddleware  — assigns / propagates a correlation ID to every request
2. LoggingMiddleware    — structured request/response logging

Logged: method, path, status, request_id, duration_ms
NOT logged: passwords, password hashes, JWT tokens, health assessment values
"""

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import request_id_ctx_var

logger = logging.getLogger("medirisk.access")

# Header names
X_REQUEST_ID = "X-Request-ID"
X_CORRELATION_ID = "X-Correlation-ID"

# Fields that must never appear in logs
_SENSITIVE_FIELDS = frozenset(
    {
        "password",
        "password_hash",
        "new_password",
        "confirm_password",
        "token",
        "access_token",
        "refresh_token",
    }
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Assigns a unique request ID to every incoming request.
    Accepts X-Request-ID / X-Correlation-ID from the client.
    Returns the assigned ID in the X-Request-ID response header.
    Sets the ID in request.state.request_id and the logging context var.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Accept from client or generate a new one
        incoming = (
            request.headers.get(X_REQUEST_ID)
            or request.headers.get(X_CORRELATION_ID)
        )
        request_id = incoming if incoming else str(uuid.uuid4())

        # Expose on request state for endpoint / error handler access
        request.state.request_id = request_id

        # Set context variable for logging
        token = request_id_ctx_var.set(request_id)
        try:
            response: Response = await call_next(request)
        finally:
            request_id_ctx_var.reset(token)

        response.headers[X_REQUEST_ID] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs method, path, status code, request ID, and execution duration.
    Does NOT log request/response bodies to prevent sensitive data leakage.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.monotonic()
        request_id = getattr(request.state, "request_id", "-")

        response: Response = await call_next(request)

        duration_ms = round((time.monotonic() - start) * 1000, 2)
        logger.info(
            "%s %s -> %s | %s ms | req=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response
