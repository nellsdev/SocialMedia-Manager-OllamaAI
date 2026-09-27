"""Agent response cache with TTL.

Backends:
- In-memory dict (default, per-process, dev)
- Redis (production, shared across workers)

Cache key = SHA-256 of (profile_id + agent_type + task + prompt)
TTL = 5 minutes by default (configurable via AGENT_CACHE_TTL_SECONDS).
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract cache
# ---------------------------------------------------------------------------

class AgentCache:
    """Backend-agnostic cache for agent responses."""

    async def get(self, key: str) -> dict[str, Any] | None:
        ...

    async def set(self, key: str, value: dict[str, Any], ttl: int) -> None:
        ...

    def make_key(
        self,
        profile_id: str,
        agent_type: str,
        task: str,
        prompt: str,
    ) -> str:
        """Deterministic cache key from request parameters."""
        payload = f"{profile_id}:{agent_type}:{task}:{prompt}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# In-memory backend (dev / single-process)
# ---------------------------------------------------------------------------

class InMemoryAgentCache(AgentCache):
    """Simple dict-based cache with manual TTL tracking.

    Not suitable for multi-process deployments.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[dict[str, Any], float]] = {}

    async def get(self, key: str) -> dict[str, Any] | None:
        import time
        entry = self._store.get(key)
        if not entry:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: dict[str, Any], ttl: int) -> None:
        import time
        self._store[key] = (value, time.time() + ttl)


# ---------------------------------------------------------------------------
# Redis backend (production)
# ---------------------------------------------------------------------------

class RedisAgentCache(AgentCache):
    """Redis-backed cache shared across workers."""

    def __init__(self, redis_url: str) -> None:
        import redis as redis_lib
        self._client = redis_lib.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> dict[str, Any] | None:
        raw = self._client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def set(self, key: str, value: dict[str, Any], ttl: int) -> None:
        self._client.setex(key, ttl, json.dumps(value, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_CACHE_INSTANCE: AgentCache | None = None


def get_agent_cache() -> AgentCache:
    """Return the singleton cache backend."""
    global _CACHE_INSTANCE
    if _CACHE_INSTANCE is None:
        if settings.REDIS_URL:
            _CACHE_INSTANCE = RedisAgentCache(settings.REDIS_URL)
            logger.info("Agent cache: Redis (%s)", settings.REDIS_URL)
        else:
            _CACHE_INSTANCE = InMemoryAgentCache()
            logger.info("Agent cache: in-memory")
    return _CACHE_INSTANCE


def reset_agent_cache() -> None:
    """Reset the singleton (useful in tests)."""
    global _CACHE_INSTANCE
    _CACHE_INSTANCE = None
