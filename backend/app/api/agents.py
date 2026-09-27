"""AI Agent API routes (3.8 / R013–R016).

Provides endpoints for caption suggestions, hashtag generation, format
recommendations, and weekly content idea generation. Routes are mounted
under ``/api/agents`` and use the Orchestrator to dispatch tasks to the
appropriate agent.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from supabase import Client

from app.agents.orchestrator import Orchestrator, AgentTask
from app.core.database import get_supabase_client
from app.core.rate_limit import get_limiter, agent_rate_limit
from app.schemas.agents import (
    CaptionRequest,
    CaptionResponse,
    CaptionOption,
    HashtagRequest,
    HashtagResponse,
    FormatRequest,
    FormatResponse,
    WeeklyIdeasResponse,
    WeeklyIdeasItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


def _get_orchestrator() -> Orchestrator:
    """Create a fresh orchestrator per request to avoid profile state leakage."""
    return Orchestrator()


def _get_supabase() -> Client:
    return get_supabase_client()


def _require_user(request: Request, supabase: Client) -> dict:
    result = supabase.auth.get_user()
    user = result.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_dict = {"id": str(user.id), "email": user.email}
    request.state.user = user_dict
    return user_dict


limiter = get_limiter()


def _require_profile(supabase: Client, user: dict) -> str:
    resp = supabase.table("profiles").select("id").eq("user_id", user["id"]).maybe_single().execute()
    if not resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return resp.data["id"]


@router.post("/captions", response_model=CaptionResponse)
@limiter.limit(agent_rate_limit())
async def suggest_captions(
    request: Request,
    body: CaptionRequest,
    supabase: Client = Depends(_get_supabase),
):
    """Generate 3 caption options tailored to the profile's strategy (R013).

    Uses ContentCreatorAgent with qwen2.5:7b via Ollama.
    """
    user = _require_user(request, supabase)
    profile_id = _require_profile(supabase, user)

    orchestrator = _get_orchestrator()
    task = AgentTask(
        task_type="captions",
        params={"post_context": body.post_context, "n": body.n},
        profile_id=profile_id,
    )
    result = await orchestrator.run_task(task)

    if result.error:
        logger.error("Agent task failed (captions): %s", result.error)
        raise HTTPException(status_code=502, detail="AI service temporarily unavailable. Please try again.")

    options = result.data or []
    # Ensure CaptionOption objects
    parsed = []
    for opt in options:
        if isinstance(opt, dict):
            parsed.append(CaptionOption(**opt))
        else:
            parsed.append(CaptionOption(text=str(opt)))

    return CaptionResponse(options=parsed)


@router.post("/hashtags", response_model=HashtagResponse)
@limiter.limit(agent_rate_limit())
async def suggest_hashtags(
    request: Request,
    body: HashtagRequest,
    supabase: Client = Depends(_get_supabase),
):
    """Suggest 5-10 hashtags for the given caption (R013)."""
    user = _require_user(request, supabase)
    profile_id = _require_profile(supabase, user)

    orchestrator = _get_orchestrator()
    task = AgentTask(
        task_type="hashtags",
        params={"caption": body.caption, "pillars": body.pillars},
        profile_id=profile_id,
    )
    result = await orchestrator.run_task(task)

    if result.error:
        logger.error("Agent task failed (hashtags): %s", result.error)
        raise HTTPException(status_code=502, detail="AI service temporarily unavailable. Please try again.")

    hashtags = result.data or []
    if isinstance(hashtags, list) and all(isinstance(h, str) for h in hashtags):
        return HashtagResponse(hashtags=hashtags)
    return HashtagResponse(hashtags=[str(h) for h in hashtags])


@router.post("/format", response_model=FormatResponse)
@limiter.limit(agent_rate_limit())
async def suggest_format(
    request: Request,
    body: FormatRequest,
    supabase: Client = Depends(_get_supabase),
):
    """Recommend the best Instagram format for a content idea (R015)."""
    user = _require_user(request, supabase)
    profile_id = _require_profile(supabase, user)

    orchestrator = _get_orchestrator()
    task = AgentTask(
        task_type="format",
        params={"idea": body.idea},
        profile_id=profile_id,
    )
    result = await orchestrator.run_task(task)

    if result.error:
        logger.error("Agent task failed (format): %s", result.error)
        raise HTTPException(status_code=502, detail="AI service temporarily unavailable. Please try again.")

    data = result.data
    if isinstance(data, dict):
        return FormatResponse(**data)
    return FormatResponse(format=getattr(data, "format", "carousel"), reasoning=getattr(data, "reasoning", ""))


@router.post("/weekly-ideas", response_model=WeeklyIdeasResponse)
@limiter.limit(agent_rate_limit())
async def generate_weekly_ideas(
    request: Request,
    supabase: Client = Depends(_get_supabase),
):
    """Generate up to 7 content ideas for the upcoming week (R014)."""
    user = _require_user(request, supabase)
    profile_id = _require_profile(supabase, user)

    orchestrator = _get_orchestrator()
    task = AgentTask(
        task_type="weekly-ideas",
        params={},
        profile_id=profile_id,
    )
    result = await orchestrator.run_task(task)

    if result.error:
        logger.error("Agent task failed (weekly-ideas): %s", result.error)
        raise HTTPException(status_code=502, detail="AI service temporarily unavailable. Please try again.")

    ideas = result.data or []
    parsed = []
    for idea in ideas:
        if isinstance(idea, dict):
            parsed.append(WeeklyIdeasItem(**idea))
        else:
            parsed.append(WeeklyIdeasItem(title=str(idea)))

    return WeeklyIdeasResponse(ideas=parsed)
