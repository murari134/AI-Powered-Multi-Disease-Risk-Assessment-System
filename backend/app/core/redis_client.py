"""
MediRisk 2.0 — Redis Client Abstraction
Phase 4: Backend Core

Provides a lazy Redis client that does NOT crash the application
when Redis is unavailable at startup.
Structured to later support caching, rate limiting, and session infra.
"""

import logging
from typing import Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level client — initialised on first use (lazy)
_redis_client: Optional[Redis] = None


def get_redis_client() -> Optional[Redis]:
    """
    Return the shared async Redis client, or None if unavailable.
    Application must not crash if Redis is offline during development.
    """
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
        except Exception as exc:
            logger.warning("Redis client creation failed: %s", exc)
            return None
    return _redis_client


async def ping_redis() -> bool:
    """
    Send a PING to Redis to test connectivity.
    Returns True if reachable, False otherwise (never raises).
    """
    client = get_redis_client()
    if client is None:
        return False
    try:
        return await client.ping()
    except (RedisError, Exception) as exc:
        logger.warning("Redis ping failed: %s", exc)
        return False


async def close_redis() -> None:
    """Close the Redis connection pool on application shutdown."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None
