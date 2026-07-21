"""Profile routes — read/write the user's profile and strategy settings.

Also serves the list of predefined creator archetypes (R002–R004).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.database import get_supabase_client
from app.schemas.profiles import (
    ARCHETYPES,
    ArchetypeResponse,
    ProfileResponse,
    StrategyUpdate,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _get_supabase() -> Client:
    return get_supabase_client()


def _require_user(supabase: Client) -> dict:
    """Get the authenticated user or raise 401."""
    result = supabase.auth.get_user()
    user = result.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"id": user.id, "email": user.email}


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(supabase: Client = Depends(_get_supabase)):
    """Get the current user's profile."""
    user = _require_user(supabase)
    resp = supabase.table("profiles").select("*").eq("user_id", user["id"]).maybe_single().execute()
    if not resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return ProfileResponse(**resp.data)


@router.put("/me/strategy", response_model=ProfileResponse)
async def update_strategy(body: StrategyUpdate, supabase: Client = Depends(_get_supabase)):
    """Update the current profile's strategy (archetype, pillars, voice, etc.)."""
    user = _require_user(supabase)

    # Build update payload with only provided fields
    update_data = {}
    for field in ("archetype", "voice_description", "content_pillars", "target_audience", "goals", "visual_references"):
        value = getattr(body, field, None)
        if value is not None:
            update_data[field] = value

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    resp = supabase.table("profiles").update(update_data).eq("user_id", user["id"]).execute()
    if not resp.data or len(resp.data) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return ProfileResponse(**resp.data[0])


@router.get("/me/archetypes", response_model=list[ArchetypeResponse])
async def list_archetypes():
    """Return the list of predefined creator archetypes (R003)."""
    return ARCHETYPES
