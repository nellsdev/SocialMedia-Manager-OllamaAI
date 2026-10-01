"""Content post routes — CRUD for Instagram posts (R011, R012).

Covers draft creation, editing, status lifecycle, scheduling, and
publishing via the SchedulerAgent (R017, R018, 4.1, 4.2, 4.3).
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from supabase import Client

from app.agents.scheduler_agent import SchedulerAgent
from app.core.auth_utils import extract_bearer_token
from app.core.database import get_supabase_client
from app.schemas.agents import ScheduleRequest, ScheduleResponse, PublishResponse
from app.schemas.posts import PostCreate, PostResponse, PostUpdate

router = APIRouter(prefix="/posts", tags=["posts"])


def _get_supabase() -> Client:
    return get_supabase_client()


def _require_user(request: Request, supabase: Client) -> dict:
    result = supabase.auth.get_user(extract_bearer_token(request))
    user = result.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"id": user.id, "email": user.email}


def _require_profile(supabase: Client, user: dict) -> str:
    from app.core.auth_utils import require_profile
    return require_profile(supabase, user["id"])


@router.get("", response_model=list[PostResponse])
async def list_posts(
    request: Request,
    status_filter: str | None = None,
    format_filter: str | None = None,
    supabase: Client = Depends(_get_supabase),
):
    """List posts with optional filters for status and format."""
    user = _require_user(request, supabase)
    profile_id = _require_profile(supabase, user)

    query = supabase.table("content_posts").select("*").eq("profile_id", profile_id)
    if status_filter:
        query = query.eq("status", status_filter)
    if format_filter:
        query = query.eq("format", format_filter)
    query = query.order("created_at", desc=True)

    resp = query.execute()
    return [PostResponse(**item) for item in (resp.data or [])]


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(request: Request, body: PostCreate, supabase: Client = Depends(_get_supabase)):
    """Create a new post draft (R011)."""
    user = _require_user(request, supabase)
    profile_id = _require_profile(supabase, user)

    post_data = {
        "id": str(uuid.uuid4()),
        "profile_id": profile_id,
        "format": body.format,
        "title": body.title or "",
        "caption": body.caption or "",
        "first_comment": body.first_comment,
        "media_urls": body.media_urls or [],
        "hashtags": body.hashtags or [],
        "status": "draft",
        "scheduled_for": body.scheduled_for.isoformat() if body.scheduled_for else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    supabase.table("content_posts").insert(post_data).execute()
    resp = supabase.table("content_posts").select("*").eq("id", post_data["id"]).single().execute()
    return PostResponse(**resp.data)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(request: Request, post_id: str, body: PostUpdate, supabase: Client = Depends(_get_supabase)):
    """Update an existing post (R012)."""
    user = _require_user(request, supabase)
    profile_id = _require_profile(supabase, user)

    # Verify ownership
    from app.core.auth_utils import maybe_single_data
    existing = maybe_single_data(
        supabase.table("content_posts").select("id").eq("id", post_id).eq("profile_id", profile_id)
    )
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    update_data = {}
    for field in ("title", "caption", "first_comment", "media_urls", "hashtags", "format", "status"):
        value = getattr(body, field, None)
        if value is not None:
            update_data[field] = value
    if body.scheduled_for is not None:
        update_data["scheduled_for"] = body.scheduled_for.isoformat()

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    supabase.table("content_posts").update(update_data).eq("id", post_id).execute()
    resp = supabase.table("content_posts").select("*").eq("id", post_id).single().execute()
    return PostResponse(**resp.data)


# ---------------------------------------------------------------------------
# Schedule / Publish (4.1, 4.2, 4.3 — R017, R018)
# ---------------------------------------------------------------------------


@router.post("/{post_id}/schedule", response_model=ScheduleResponse)
async def schedule_post(
    request: Request,
    post_id: str,
    body: ScheduleRequest,
    supabase: Client = Depends(_get_supabase),
):
    """Schedule a post for automatic publishing (R017).

    Accepts an ISO 8601 datetime string. Validates that the timestamp is
    in the future. Registers an APScheduler job via SchedulerAgent.
    """
    user = _require_user(request, supabase)
    profile_id = _require_profile(supabase, user)

    # Verify post ownership and current status
    existing = (
        supabase.table("content_posts")
        .select("id, status, format, ig_account_id")
        .eq("id", post_id)
        .eq("profile_id", profile_id)
        .maybe_single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    post = existing.data
    if post["status"] not in ("draft", "scheduled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot schedule post with status '{post['status']}'",
        )

    # Parse and validate scheduled time
    try:
        scheduled_for = datetime.fromisoformat(body.scheduled_for)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid datetime format")

    if scheduled_for.tzinfo is None:
        # Treat as UTC if no timezone provided
        scheduled_for = scheduled_for.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    if scheduled_for <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot schedule in the past",
        )

    # Register with SchedulerAgent
    agent = SchedulerAgent()
    job_id = await agent.schedule_post(post_id, scheduled_for)

    # Update post status and scheduled_for
    update_data = {
        "status": "scheduled",
        "scheduled_for": scheduled_for.isoformat(),
    }
    supabase.table("content_posts").update(update_data).eq("id", post_id).execute()

    # Create scheduler_jobs record
    scheduler_job_data = {
        "id": str(uuid.uuid4()),
        "post_id": post_id,
        "job_id": job_id,
        "scheduled_at": scheduled_for.isoformat(),
        "status": "pending",
        "retry_count": 0,
    }
    supabase.table("scheduler_jobs").insert(scheduler_job_data).execute()

    return ScheduleResponse(status="scheduled", job_id=job_id)


@router.post("/{post_id}/publish", response_model=PublishResponse)
async def publish_post_now(
    request: Request,
    post_id: str,
    supabase: Client = Depends(_get_supabase),
):
    """Publish a post immediately (R018).

    Uses SchedulerAgent.publish_post which retries on failure with
    exponential back-off (max 3 retries). Updates post status accordingly.
    """
    user = _require_user(request, supabase)
    profile_id = _require_profile(supabase, user)

    # Verify post ownership
    existing = (
        supabase.table("content_posts")
        .select("id, status")
        .eq("id", post_id)
        .eq("profile_id", profile_id)
        .maybe_single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    post = existing.data
    if post["status"] == "published":
        return PublishResponse(
            status="already_published",
            failure_reason="Post is already published",
        )

    # Publish via SchedulerAgent
    agent = SchedulerAgent()
    result = await agent.publish_post(post_id)

    return PublishResponse(
        status=result.status,
        platform_post_id=result.platform_post_id,
        platform_permalink=result.platform_permalink,
        failure_reason=result.failure_reason,
    )


@router.post("/{post_id}/retry", response_model=PublishResponse)
async def retry_publish(
    request: Request,
    post_id: str,
    supabase: Client = Depends(_get_supabase),
):
    """Retry publishing a failed post (4.3 / R018)."""
    user = _require_user(request, supabase)
    profile_id = _require_profile(supabase, user)

    existing = (
        supabase.table("content_posts")
        .select("id, status")
        .eq("id", post_id)
        .eq("profile_id", profile_id)
        .maybe_single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    agent = SchedulerAgent()
    result = await agent.retry_failed(post_id)

    return PublishResponse(
        status=result.status,
        platform_post_id=result.platform_post_id,
        platform_permalink=result.platform_permalink,
        failure_reason=result.failure_reason,
    )
