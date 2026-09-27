"""FastAPI application entry-point.

Registers all routers, configures CORS, and provides health-check endpoint.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api import agents, auth, dashboard, grid, ideas, posts, profiles, social, whatsapp
from app.core.config import settings
from app.core.rate_limit import get_limiter

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="MVP — Personal Profile + Instagram social media manager",
)

# ---------------------------------------------------------------------------
# Rate limiting (slowapi)
# ---------------------------------------------------------------------------

limiter = get_limiter()
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please slow down."},
    )

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ---------------------------------------------------------------------------
# Routers — all mounted under /api prefix
# ---------------------------------------------------------------------------

app.include_router(auth.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")
app.include_router(social.router, prefix="/api")
app.include_router(ideas.router, prefix="/api")
app.include_router(posts.router, prefix="/api")
app.include_router(grid.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(whatsapp.router, prefix="/api")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    from datetime import datetime, timezone
    checks = {}
    healthy = True

    # Check Supabase
    try:
        from app.core.database import get_supabase_client
        db = get_supabase_client()
        db.table("profiles").select("id").limit(1).execute()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:100]}"
        healthy = False

    # Check Ollama
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                checks["ollama"] = "ok"
            else:
                checks["ollama"] = f"error: status {resp.status_code}"
                healthy = False
    except Exception as e:
        checks["ollama"] = f"error: {str(e)[:100]}"
        healthy = False

    # Check scheduler
    try:
        from app.agents.scheduler_agent import get_scheduler
        scheduler = get_scheduler()
        checks["scheduler"] = "ok" if scheduler.running else "stopped"
        if not scheduler.running:
            healthy = False
    except Exception as e:
        checks["scheduler"] = f"error: {str(e)[:100]}"
        healthy = False

    status_code = 200 if healthy else 503
    return {
        "status": "ok" if healthy else "degraded",
        "app": settings.APP_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
