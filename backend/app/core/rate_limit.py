"""Rate limiting for agent and API endpoints.

Uses slowapi (Redis-backed in production, in-memory in dev).
In-memory fallback is per-process, so it works for single-server
deployments. For multi-server production, set REDIS_URL.
"""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Key func: identify by authenticated user when available, fall back to IP
# ---------------------------------------------------------------------------

def _rate_limit_key(request: Request) -> str:
    """Return a rate-limit key.

    Uses the Supabase user id from the Authorization header when available,
    otherwise falls back to the client's IP address.
    """
    # Try to extract user id from the Supabase session injected by dependency
    user = getattr(request.state, "user", None)
    if user and isinstance(user, dict) and user.get("id"):
        return f"user:{user['id']}"

    # Fallback to IP address
    return get_remote_address(request)


# ---------------------------------------------------------------------------
# Limiter singleton
# ---------------------------------------------------------------------------

_limiter_instance: Limiter | None = None


def get_limiter() -> Limiter:
    """Return the configured rate limiter.

    Uses Redis when ``REDIS_URL`` is set, otherwise in-memory (per-process).
    """
    global _limiter_instance
    if _limiter_instance is None:
        storage_uri = settings.REDIS_URL or "memory://"
        _limiter_instance = Limiter(
            key_func=_rate_limit_key,
            storage_uri=storage_uri,
            default_limits=[],
        )
        logger.info("Rate limiter initialized: %s", storage_uri)
    return _limiter_instance


def agent_rate_limit() -> list[str]:
    """Return the rate limit string for agent endpoints.

    Example: ``10/minute`` with burst of 3.
    """
    rpm = settings.RATE_LIMIT_AGENTS_PER_MINUTE
    burst = settings.RATE_LIMIT_AGENTS_BURST
    return [f"{rpm}/minute;burst={burst}"]
