"""FastAPI application entry-point.

Registers all routers, configures CORS, and provides health-check endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, auth, grid, ideas, posts, profiles, social, whatsapp
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="MVP — Personal Profile + Instagram social media manager",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(agents.router, prefix="/api")
app.include_router(whatsapp.router, prefix="/api")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
