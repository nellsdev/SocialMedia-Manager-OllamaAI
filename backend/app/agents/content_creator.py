"""Content Creator Agent (3.3).

Generates captions, hashtags, format recommendations, and weekly content
ideas via Ollama using the **qwen2.5:7b** model. Every prompt is tailored
to the profile's archetype, voice description, and content pillars.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Few-shot / memory helpers
# ---------------------------------------------------------------------------

def _fetch_recent_captions(profile_id: str, limit: int = 3) -> list[str]:
    """Load the most recent published captions for this profile from Supabase.

    Returns an empty list on any error so the agent degrades gracefully.
    """
    try:
        from app.core.database import get_supabase_service_client
        supabase = get_supabase_service_client()
        resp = (
            supabase.table("content_posts")
            .select("caption")
            .eq("profile_id", profile_id)
            .eq("status", "published")
            .not_.is_("caption", "null")
            .neq("caption", "")
            .order("published_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [row["caption"] for row in (resp.data or []) if row.get("caption")]
    except Exception as exc:
        logger.debug("Could not fetch recent captions for %s: %s", profile_id, exc)
        return []

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CaptionSuggestion:
    text: str
    tone: str = ""
    length: str = ""
    pillar: str = ""


@dataclass
class FormatRecommendation:
    format: str  # story / carousel / reel / live
    reasoning: str = ""


@dataclass
class ContentIdea:
    title: str
    description: str = ""
    suggested_format: str = ""
    content_pillar: str = ""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class ContentCreatorAgent(BaseAgent):
    """Generates creative content suggestions using qwen2.5:7b via Ollama.

    Requires the Ollama server to be running at ``http://localhost:11434``.
    """

    MODEL = "qwen2.5:7b"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def suggest_captions(
        self,
        post_context: str,
        n: int = 3,
    ) -> list[CaptionSuggestion]:
        """Return *n* caption suggestions for the given post context."""
        # Fetch few-shot examples from published posts
        few_shot: list[str] = []
        if self._profile:
            few_shot = _fetch_recent_captions(self._profile.profile_id, limit=3)

        prompt = self._build_caption_prompt(post_context, n, few_shot)
        raw = await self._ollama_generate(prompt, task_type="captions")
        return self._parse_captions(raw, n)

    async def suggest_hashtags(
        self,
        caption: str,
        pillars: list[str] | None = None,
    ) -> list[str]:
        """Return 5–10 hashtag suggestions for the given caption."""
        prompt = self._build_hashtag_prompt(caption, pillars or [])
        raw = await self._ollama_generate(prompt, task_type="hashtags")
        return self._parse_hashtags(raw)

    async def suggest_format(
        self,
        idea: str,
    ) -> FormatRecommendation:
        """Recommend the best Instagram format for a content idea."""
        prompt = self._build_format_prompt(idea)
        raw = await self._ollama_generate(prompt, task_type="format")
        return self._parse_format(raw)

    async def generate_weekly_ideas(self) -> list[ContentIdea]:
        """Generate up to 7 content ideas (one per day) for the week ahead."""
        if (
            not self._profile
            or not self._profile.content_pillars
            or not self._profile.archetype
        ):
            return []
        prompt = self._build_weekly_ideas_prompt()
        raw = await self._ollama_generate(prompt, task_type="weekly-ideas")
        return self._parse_weekly_ideas(raw)

    async def run(self, **kwargs) -> object:
        """Generic execution dispatcher.

        Supported task types: captions, hashtags, format, weekly-ideas.
        """
        task = kwargs.get("task", "captions")
        if task == "captions":
            return await self.suggest_captions(
                post_context=kwargs.get("post_context", ""),
                n=kwargs.get("n", 3),
            )
        if task == "hashtags":
            return await self.suggest_hashtags(
                caption=kwargs.get("caption", ""),
                pillars=kwargs.get("pillars"),
            )
        if task == "format":
            return await self.suggest_format(idea=kwargs.get("idea", ""))
        if task == "weekly-ideas":
            return await self.generate_weekly_ideas()
        raise ValueError(f"Unknown task: {task}")

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_caption_prompt(self, post_context: str, n: int, few_shot: list[str] | None = None) -> str:
        profile = self._profile
        parts = [
            f"You are a social media content creator with archetype: {profile.archetype if profile else 'personal_sharing'}.",
        ]
        if profile:
            if profile.voice_description:
                parts.append(f"Tone / voice: {profile.voice_description}")
            if profile.content_pillars:
                parts.append(f"Content pillars: {', '.join(profile.content_pillars)}")
                parts.append(
                    "STRICT RULE: Every caption MUST align with one of the content pillars above. "
                    "If an idea does not fit any pillar, do not include it."
                )
            if profile.target_audience:
                parts.append(f"Target audience: {profile.target_audience}")
            if profile.goals:
                parts.append(f"Goals: {profile.goals}")

        # Few-shot examples from previously published captions
        if few_shot:
            parts.append("")
            parts.append("Recent captions from this creator (match this tone and style):")
            for i, caption in enumerate(few_shot, 1):
                parts.append(f'{i}. "{caption[:200]}"')

        parts.append("")
        parts.append(f"Suggest exactly {n} Instagram captions for the following post context.")
        parts.append(f"Post context: {post_context}")
        parts.append("")
        parts.append(
            'Return ONLY a JSON array of objects with keys "text", "tone", "length", and "pillar". '
            "No markdown, no explanation, no extra text."
        )
        return "\n".join(parts)

    def _build_hashtag_prompt(self, caption: str, pillars: list[str]) -> str:
        parts = [
            "You are an Instagram hashtag strategist.",
            "",
            f"Caption: {caption}",
        ]
        if pillars:
            parts.append(f"Content pillars: {', '.join(pillars)}")
        parts.append("")
        parts.append(
            "Suggest 5-10 relevant hashtags that combine niche, trending, and pillar tags. "
            "Return ONLY a JSON array of strings. No markdown, no explanation."
        )
        return "\n".join(parts)

    def _build_format_prompt(self, idea: str) -> str:
        parts = [
            "You are an Instagram format strategist.",
            "",
            f"Content idea: {idea}",
        ]
        if self._profile:
            if self._profile.archetype:
                parts.append(f"Creator archetype: {self._profile.archetype}")
            if self._profile.target_audience:
                parts.append(f"Audience: {self._profile.target_audience}")
        parts.append("")
        parts.append(
            "Recommend ONE Instagram format (story, carousel, reel, or live) for this idea. "
            'Return ONLY a JSON object with keys "format" and "reasoning". No markdown.'
        )
        return "\n".join(parts)

    def _build_weekly_ideas_prompt(self) -> str:
        profile = self._profile
        today = datetime.utcnow().strftime("%Y-%m-%d")
        valid_pillars = profile.content_pillars if profile and profile.content_pillars else []
        parts = [
            f"You are a social media content strategist. Today is {today}.",
        ]
        if profile:
            if profile.archetype:
                parts.append(f"Archetype: {profile.archetype}")
            if profile.voice_description:
                parts.append(f"Voice: {profile.voice_description}")
            if valid_pillars:
                parts.append(f"Content pillars: {', '.join(valid_pillars)}")
            if profile.target_audience:
                parts.append(f"Target audience: {profile.target_audience}")
        parts.append("")
        parts.append(
            "Generate up to 7 content ideas for the upcoming week (one per day). "
            "Spread them across the content pillars. "
        )
        if valid_pillars:
            parts.append(
                f"STRICT RULE: Every idea MUST use exactly one of these pillars: {', '.join(valid_pillars)}. "
                "If an idea does not fit any pillar, do not include it. "
                "The 'content_pillar' field in your response MUST match one of the listed pillars exactly."
            )
        parts.append("")
        parts.append(
            'Return ONLY a JSON array of objects with keys "title", "description", "suggested_format", and "content_pillar". '
            "No markdown, no explanation."
        )
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Ollama client
    # ------------------------------------------------------------------

    async def _ollama_generate(self, prompt: str, task_type: str = "") -> str:
        """Send a prompt to Ollama and return the raw response text.

        Checks the agent cache first. Retries up to 3 times on transient errors.
        Saves the interaction to agent memory when ``task_type`` is provided.
        """
        import time
        import httpx
        from tenacity import (
            retry,
            stop_after_attempt,
            wait_exponential,
            retry_if_exception_type,
        )
        from app.core.agent_cache import get_agent_cache
        from app.core.config import settings

        cache = get_agent_cache()
        cache_key = ""
        if task_type and self._profile:
            cache_key = cache.make_key(
                profile_id=self._profile.profile_id,
                agent_type=self.__class__.__name__,
                task=task_type,
                prompt=prompt,
            )
            cached = await cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for %s/%s", self.__class__.__name__, task_type)
                return cached.get("response", "")

        start = time.perf_counter()

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            retry=retry_if_exception_type(
                (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)
            ),
        )
        async def _call() -> str:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                }
                from app.core.config import settings
                resp = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "")

        raw = ""
        try:
            raw = await _call()
        finally:
            latency_ms = int((time.perf_counter() - start) * 1000)
            if task_type:
                await self._save_interaction(
                    task=task_type,
                    prompt=prompt,
                    response=raw,
                    model=self.MODEL,
                    latency_ms=latency_ms,
                )
            if cache_key:
                try:
                    await cache.set(
                        cache_key,
                        {"response": raw},
                        ttl=settings.AGENT_CACHE_TTL_SECONDS,
                    )
                except Exception:
                    pass  # Cache is best-effort
        return raw

    # ------------------------------------------------------------------
    # Parsers
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _valid_pillars(self) -> set[str]:
        """Return the set of valid pillar names for the current profile."""
        if self._profile and self._profile.content_pillars:
            return {p.lower() for p in self._profile.content_pillars}
        return set()

    def _validate_pillar(self, pillar: str) -> str:
        """Ensure a pillar value is in the profile's allowed set.

        Returns the original if valid, otherwise tries case-insensitive match,
        or returns an empty string if no match is found.
        """
        if not pillar:
            return ""
        valid = self._valid_pillars()
        if not valid:
            return pillar  # No restriction when profile has no pillars
        lowered = pillar.lower()
        if lowered in valid:
            # Return the canonical casing from the profile
            for original in self._profile.content_pillars or []:
                if original.lower() == lowered:
                    return original
        logger.warning("Pillar '%s' rejected — not in valid pillars: %s", pillar, valid)
        return ""

    def _parse_captions(self, raw: str, n: int) -> list[CaptionSuggestion]:
        """Parse the Ollama response into CaptionSuggestion objects."""
        cleaned = self._clean_json(raw)
        try:
            items = json.loads(cleaned)
            if isinstance(items, dict):
                items = [items]
            results = []
            for item in (items or []):
                if not item.get("text"):
                    continue
                validated_pillar = self._validate_pillar(item.get("pillar", ""))
                results.append(
                    CaptionSuggestion(
                        text=item.get("text", ""),
                        tone=item.get("tone", ""),
                        length=item.get("length", ""),
                        pillar=validated_pillar,
                    )
                )
            return results[:n]
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to parse captions: %s — raw: %s", exc, raw[:200])
            return [CaptionSuggestion(text=raw.strip())]

    def _parse_hashtags(self, raw: str) -> list[str]:
        """Parse the Ollama response into a list of hashtag strings."""
        cleaned = self._clean_json(raw)
        try:
            items = json.loads(cleaned)
            if isinstance(items, str):
                # Sometimes the model returns a single comma-separated string
                items = [h.strip().lstrip("#") for h in items.split(",") if h.strip()]
            return [
                h.lstrip("#") if isinstance(h, str) else str(h)
                for h in (items or [])
            ][:10]
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to parse hashtags: %s — raw: %s", exc, raw[:200])
            # Fallback: extract #-prefixed words
            import re

            return re.findall(r"#(\w+)", raw)[:10]

    def _parse_format(self, raw: str) -> FormatRecommendation:
        """Parse the Ollama response into a FormatRecommendation."""
        cleaned = self._clean_json(raw)
        try:
            data = json.loads(cleaned)
            return FormatRecommendation(
                format=data.get("format", "carousel"),
                reasoning=data.get("reasoning", ""),
            )
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to parse format: %s — raw: %s", exc, raw[:200])
            return FormatRecommendation(format="carousel", reasoning=raw.strip())

    def _parse_weekly_ideas(self, raw: str) -> list[ContentIdea]:
        """Parse the Ollama response into ContentIdea objects."""
        cleaned = self._clean_json(raw)
        try:
            items = json.loads(cleaned)
            if isinstance(items, dict):
                items = [items]
            results = []
            for item in (items or []):
                if not item.get("title"):
                    continue
                validated_pillar = self._validate_pillar(item.get("content_pillar", ""))
                # If pillar is invalid and we have strict pillars, skip the idea
                if self._valid_pillars() and not validated_pillar:
                    logger.warning(
                        "Weekly idea '%s' skipped — invalid pillar '%s'",
                        item.get("title", "")[:40],
                        item.get("content_pillar", ""),
                    )
                    continue
                results.append(
                    ContentIdea(
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                        suggested_format=item.get("suggested_format", ""),
                        content_pillar=validated_pillar,
                    )
                )
            return results[:7]
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to parse weekly ideas: %s — raw: %s", exc, raw[:200])
            return [ContentIdea(title=raw.strip())]

    @staticmethod
    def _clean_json(raw: str) -> str:
        """Strip markdown code fences and leading/trailing whitespace."""
        raw = raw.strip()
        if raw.startswith("```"):
            # Remove opening fence + optional language hint
            first_nl = raw.find("\n")
            if first_nl != -1:
                raw = raw[first_nl + 1 :]
            # Remove closing fence
            if raw.endswith("```"):
                raw = raw[:-3].strip()
        return raw
