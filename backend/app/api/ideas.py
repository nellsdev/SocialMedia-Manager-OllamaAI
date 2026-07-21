"""Idea bank routes — CRUD for content ideas, WhatsApp webhook (4.5),
and conversion to draft posts.

Covers R005 (in-app capture), R007 (management, filtering, convert),
and R023-R024 (WhatsApp webhook).
"""

import hmac
import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from supabase import Client

from app.agents.idea_bank import IdeaBankAgent
from app.core.config import settings
from app.core.database import get_supabase_client
from app.schemas.ideas import IdeaConvertResponse, IdeaCreate, IdeaResponse
from app.schemas.whatsapp import WhatsAppMessageRequest

router = APIRouter(prefix="/ideas", tags=["ideas"])


def _get_supabase() -> Client:
    return get_supabase_client()


def _require_user(supabase: Client) -> dict:
    result = supabase.auth.get_user()
    user = result.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"id": user.id, "email": user.email}


def _require_profile(supabase: Client, user: dict) -> str:
    """Get profile_id for the current user."""
    resp = supabase.table("profiles").select("id").eq("user_id", user["id"]).maybe_single().execute()
    if not resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return resp.data["id"]


@router.get("", response_model=list[IdeaResponse])
async def list_ideas(
    pillar: str | None = Query(None),
    status: str | None = Query(None),
    source: str | None = Query(None),
    supabase: Client = Depends(_get_supabase),
):
    """List ideas with optional filters for pillar, status, and source (R005, R007)."""
    user = _require_user(supabase)
    profile_id = _require_profile(supabase, user)

    query = supabase.table("content_ideas").select("*").eq("profile_id", profile_id)
    if pillar:
        query = query.eq("content_pillar", pillar)
    if status:
        query = query.eq("status", status)
    if source:
        query = query.eq("source", source)
    query = query.order("created_at", desc=True)

    resp = query.execute()
    return [IdeaResponse(**item) for item in (resp.data or [])]


@router.post("", response_model=IdeaResponse, status_code=status.HTTP_201_CREATED)
async def create_idea(body: IdeaCreate, supabase: Client = Depends(_get_supabase)):
    """Create a new content idea (R005)."""
    user = _require_user(supabase)
    profile_id = _require_profile(supabase, user)

    idea_data = {
        "id": str(uuid.uuid4()),
        "profile_id": profile_id,
        "title": body.title,
        "description": body.description or "",
        "suggested_format": body.suggested_format,
        "content_pillar": body.content_pillar,
        "source": "manual",
        "status": "idea",
        "created_at": datetime.utcnow().isoformat(),
    }

    supabase.table("content_ideas").insert(idea_data).execute()
    resp = supabase.table("content_ideas").select("*").eq("id", idea_data["id"]).single().execute()
    return IdeaResponse(**resp.data)


@router.put("/{idea_id}/convert", response_model=IdeaConvertResponse)
async def convert_idea(idea_id: str, supabase: Client = Depends(_get_supabase)):
    """Convert an idea into a draft post (R007, R010).

    Creates a new content_post prefilled with the idea's data, marks the idea
    as converted, and links them.
    """
    user = _require_user(supabase)
    profile_id = _require_profile(supabase, user)

    # Fetch the idea
    idea_resp = supabase.table("content_ideas").select("*").eq("id", idea_id).eq("profile_id", profile_id).maybe_single().execute()
    if not idea_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found")

    idea = idea_resp.data
    if idea["status"] == "converted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idea already converted")

    # Create a draft post from the idea
    post_id = str(uuid.uuid4())
    post_data = {
        "id": post_id,
        "profile_id": profile_id,
        "format": idea.get("suggested_format") or "carousel",
        "title": idea["title"],
        "caption": idea.get("description") or "",
        "status": "draft",
        "created_at": datetime.utcnow().isoformat(),
    }
    supabase.table("content_posts").insert(post_data).execute()

    # Mark idea as converted
    supabase.table("content_ideas").update({
        "status": "converted",
        "converted_to": post_id,
    }).eq("id", idea_id).execute()

    return IdeaConvertResponse(post_id=post_id)


# ---------------------------------------------------------------------------
# WhatsApp Webhook (4.5 — R023, R024)
# ---------------------------------------------------------------------------


@router.post("/whatsapp", response_model=IdeaResponse)
async def whatsapp_webhook(
    body: WhatsAppMessageRequest,
    request: Request,
    supabase: Client = Depends(_get_supabase),
):
    """Receive forwarded WhatsApp messages and create ideas (R024).

    This endpoint is called by the WhatsApp Cloud API webhook when the user
    forwards a message to their configured WhatsApp number. It can also be
    called directly from the app for testing.

    The IdeaBankAgent processes the message text to auto-tag the pillar and
    suggest a format before creating the idea.
    """
    # Verify WhatsApp webhook signature
    if settings.WHATSAPP_WEBHOOK_SECRET:
        signature = request.headers.get("X-Hub-Signature-256", "")
        raw_body = await request.body()
        expected = hmac.new(
            settings.WHATSAPP_WEBHOOK_SECRET.encode(),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(f"sha256={expected}", signature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature",
            )

    # For WhatsApp webhook, use the first active profile
    profile_resp = supabase.table("profiles").select("id").limit(1).execute()
    if not profile_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile found")
    profile_id = profile_resp.data[0]["id"]

    # Load profile strategy for the agent
    profile_full = supabase.table("profiles").select("*").eq("id", profile_id).maybe_single().execute()
    profile_data = profile_full.data or {}

    from app.agents.base import ProfileStrategy

    profile_strategy = ProfileStrategy(
        profile_id=profile_id,
        archetype=profile_data.get("archetype", "personal_sharing"),
        voice_description=profile_data.get("voice_description"),
        content_pillars=profile_data.get("content_pillars"),
        target_audience=profile_data.get("target_audience"),
        goals=profile_data.get("goals"),
    )

    # Use IdeaBankAgent to process the message
    agent = IdeaBankAgent(profile=profile_strategy)
    idea = await agent.process_whatsapp_message(
        text=body.message,
        media=body.media,
    )

    # Persist to database
    now = datetime.now(timezone.utc).isoformat()
    idea_data = {
        "id": str(uuid.uuid4()),
        "profile_id": profile_id,
        "title": idea.title,
        "description": idea.description,
        "suggested_format": idea.suggested_format,
        "content_pillar": idea.content_pillar,
        "source": "whatsapp",
        "media_refs": idea.media_refs or [],
        "status": "idea",
        "created_at": now,
    }
    supabase.table("content_ideas").insert(idea_data).execute()
    resp = supabase.table("content_ideas").select("*").eq("id", idea_data["id"]).single().execute()

    return IdeaResponse(**resp.data)
