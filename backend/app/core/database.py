"""Supabase client singleton and SQLAlchemy engine.

For multi-user RLS queries the backend uses the Supabase client (anon key).
For server-side operations (scheduling, webhooks) the service-key client is
used. SQLAlchemy is used for local ORM convenience during development —
deployed environments may rely entirely on supabase-py for RLS.
"""

from supabase import Client, create_client
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


# ---------------------------------------------------------------------------
# Supabase clients
# ---------------------------------------------------------------------------

_supabase_anon: Client | None = None
_supabase_service: Client | None = None


def get_supabase_client() -> Client:
    """Return a Supabase client authenticated with the anon key."""
    global _supabase_anon
    if _supabase_anon is None:
        _supabase_anon = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_ANON_KEY,
        )
    return _supabase_anon


def get_supabase_service_client() -> Client:
    """Return a Supabase client authenticated with the service role key."""
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_KEY,
        )
    return _supabase_service


# ---------------------------------------------------------------------------
# SQLAlchemy (local ORM)
# ---------------------------------------------------------------------------

engine = create_engine(settings.SUPABASE_URL.replace(
    "http://", "postgresql://"
) if settings.SUPABASE_URL.startswith("http") else settings.SUPABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Yield a SQLAlchemy session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
