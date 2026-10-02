"""Trend data source abstraction.

Provides a stable interface for trend and reference-account research so the
app can swap implementations without touching callers:

- ``KnowledgeTrendSource`` — uses the LLM's training knowledge (current MVP
  choice; instant, free, works offline).
- ``InstagramGraphTrendSource`` — future implementation backed by the
  Instagram Graph API for live, real-world data (not implemented yet).

Callers always go through ``TrendDataSourceFactory.get()``.
"""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class TrendTopicData:
    topic: str
    description: str = ""
    relevance: str = ""  # high / medium / low


@dataclass
class ReferenceAccountAnalysis:
    username: str
    what_works: str = ""
    content_formats: str = ""
    engagement_style: str = ""
    differentiator: str = ""


@dataclass
class NicheAnalysis:
    niche: str
    trending_topics: list[TrendTopicData] = field(default_factory=list)
    trending_hashtags: list[str] = field(default_factory=list)
    reference_accounts: list[ReferenceAccountAnalysis] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> dict:
        return {
            "niche": self.niche,
            "trending_topics": [
                {"topic": t.topic, "description": t.description, "relevance": t.relevance}
                for t in self.trending_topics
            ],
            "trending_hashtags": self.trending_hashtags,
            "reference_accounts": [
                {
                    "username": a.username,
                    "what_works": a.what_works,
                    "content_formats": a.content_formats,
                    "engagement_style": a.engagement_style,
                    "differentiator": a.differentiator,
                }
                for a in self.reference_accounts
            ],
            "opportunities": self.opportunities,
            "recommendation": self.recommendation,
        }


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------


class TrendDataSource(ABC):
    """Contract every trend source must implement."""

    @abstractmethod
    async def trending_hashtags(self, pillars: list[str]) -> list[str]:
        """Return trending hashtags for the given content pillars."""

    @abstractmethod
    async def trending_topics(self, niche: str) -> list[TrendTopicData]:
        """Return trending topics for a niche."""

    @abstractmethod
    async def analyze_reference_accounts(
        self, niche: str, accounts: list[str]
    ) -> NicheAnalysis:
        """Analyze well-known accounts in the niche and produce a full analysis."""


# ---------------------------------------------------------------------------
# Knowledge-based implementation (MVP default)
# ---------------------------------------------------------------------------


class KnowledgeTrendSource(TrendDataSource):
    """Uses Ollama's training knowledge for trend research.

    Fast, free, and works without external credentials. Has a knowledge
    cutoff; not live data. Swap via the factory when wanting live data.
    """

    MODEL = "qwen2.5:7b"

    async def trending_hashtags(self, pillars: list[str]) -> list[str]:
        prompt = (
            "You are an Instagram trend analyst. Suggest trending hashtags for the "
            f"following content pillars: {', '.join(pillars)}.\n\n"
            "Return ONLY a JSON array of strings (hashtags without the # symbol). "
            "No markdown, no explanation."
        )
        raw = await self._ollama_generate(prompt)
        try:
            items = json.loads(self._clean_json(raw))
            if isinstance(items, str):
                items = [h.strip().lstrip("#") for h in items.split(",") if h.strip()]
            return [str(h).lstrip("#") for h in (items or [])][:10]
        except (json.JSONDecodeError, TypeError):
            return []

    async def trending_topics(self, niche: str) -> list[TrendTopicData]:
        prompt = (
            f"You are a social media trend researcher focused on the niche: {niche}.\n\n"
            "Suggest 5 currently relevant trending topics or content angles. "
            'Return ONLY a JSON array of objects with keys "topic", "description", '
            'and "relevance" (high/medium/low). No markdown, no explanation.'
        )
        raw = await self._ollama_generate(prompt)
        try:
            items = json.loads(self._clean_json(raw))
            if isinstance(items, dict):
                items = [items]
            return [
                TrendTopicData(
                    topic=item.get("topic", ""),
                    description=item.get("description", ""),
                    relevance=item.get("relevance", ""),
                )
                for item in (items or [])
                if item.get("topic")
            ][:8]
        except (json.JSONDecodeError, TypeError):
            return []

    async def analyze_reference_accounts(
        self, niche: str, accounts: list[str], language: str = "español"
    ) -> NicheAnalysis:
        """Full niche analysis: topics, hashtags, reference accounts, gaps."""
        prompt = self._build_niche_analysis_prompt(niche, accounts, language)
        raw = await self._ollama_generate(prompt)
        return self._parse_niche_analysis(raw, niche)

    # ------------------------------------------------------------------
    # Prompt + parser
    # ------------------------------------------------------------------

    def _build_niche_analysis_prompt(
        self, niche: str, accounts: list[str], language: str = "español"
    ) -> str:
        parts = [
            f"You are a social media strategist specialized in the niche: {niche}.",
            "",
            "Produce a complete strategic analysis of this niche for a new creator "
            "who wants to enter it or improve their presence.",
        ]
        if accounts:
            parts.append(
                "Reference accounts the creator follows: "
                + ", ".join(accounts)
                + ". Include these (plus other well-known accounts you know) in "
                "the analysis."
            )
        else:
            parts.append(
                "The creator did not name specific accounts; pick the 4-6 most "
                "well-known accounts in this niche."
            )
        parts.append("")
        parts.append(
            'Return ONLY a JSON object with keys: '
            '"niche" (string), '
            '"trending_topics" (array of {topic, description, relevance}), '
            '"trending_hashtags" (array of strings), '
            '"reference_accounts" (array of {username, what_works, content_formats, '
            'engagement_style, differentiator} for 4-6 accounts), '
            '"opportunities" (array of strings describing gaps and under-covered angles), '
            '"recommendation" (string, the overall content strategy recommendation). '
            "No markdown, no explanation."
        )
        parts.append("")
        parts.append(
            f"IMPORTANT: The creator's language is {language}. Write EVERY string "
            "field (topics, hashtags, account analysis, opportunities, "
            "recommendation) in that language. Do not translate usernames."
        )
        return "\n".join(parts)

    def _parse_niche_analysis(self, raw: str, fallback_niche: str) -> NicheAnalysis:
        data = self._parse_json(raw)
        if data is None:
            logger.warning("Failed to parse niche analysis — raw: %s", raw[:200])
            return NicheAnalysis(niche=fallback_niche)

        return NicheAnalysis(
            niche=data.get("niche") or fallback_niche,
            trending_topics=[
                TrendTopicData(
                    topic=t.get("topic", ""),
                    description=t.get("description", ""),
                    relevance=t.get("relevance", ""),
                )
                for t in (data.get("trending_topics") or [])
                if t.get("topic")
            ],
            trending_hashtags=[str(h) for h in (data.get("trending_hashtags") or [])],
            reference_accounts=[
                ReferenceAccountAnalysis(
                    username=a.get("username", ""),
                    what_works=a.get("what_works", ""),
                    content_formats=a.get("content_formats", ""),
                    engagement_style=a.get("engagement_style", ""),
                    differentiator=a.get("differentiator", ""),
                )
                for a in (data.get("reference_accounts") or [])
                if a.get("username")
            ],
            opportunities=[str(o) for o in (data.get("opportunities") or [])],
            recommendation=data.get("recommendation", ""),
        )

    # ------------------------------------------------------------------
    # Ollama client (same retry pattern as other agents)
    # ------------------------------------------------------------------

    async def _ollama_generate(self, prompt: str) -> str:
        import httpx
        from tenacity import (
            retry,
            stop_after_attempt,
            wait_exponential,
            retry_if_exception_type,
        )

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            retry=retry_if_exception_type(
                (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)
            ),
        )
        async def _call() -> str:
            async with httpx.AsyncClient(timeout=300.0) as client:
                payload = {
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                }
                resp = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "")

        return await _call()

    @staticmethod
    def _clean_json(raw: str) -> str:
        raw = raw.strip()
        if raw.startswith("```"):
            first_nl = raw.find("\n")
            if first_nl != -1:
                raw = raw[first_nl + 1 :]
            if raw.endswith("```"):
                raw = raw[:-3].strip()
        return raw

    @classmethod
    def _parse_json(cls, raw: str):
        """Parse JSON tolerantly: strip fences, repair single-quoted JSON.

        Some models emit single quotes instead of double quotes; this repairs
        the common cases (keys and string values) before json.loads.
        """
        cleaned = cls._clean_json(raw)
        try:
            return json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            # The model sometimes emits Python-style single-quoted JSON;
            # ast.literal_eval safely converts those literals to objects.
            try:
                import ast
                return ast.literal_eval(cleaned)
            except (ValueError, SyntaxError):
                return None


# ---------------------------------------------------------------------------
# Factory (single swap point for live data later)
# ---------------------------------------------------------------------------


class TrendDataSourceFactory:
    """Returns the configured trend source.

    Set ``TREND_SOURCE_LIVE=true`` in the environment to use a live
    implementation once ``InstagramGraphTrendSource`` exists.
    """

    @staticmethod
    def get(use_live: bool | None = None) -> TrendDataSource:
        if use_live is None:
            use_live = getattr(settings, "TREND_SOURCE_LIVE", False)
        if use_live:
            # Swap point: return InstagramGraphTrendSource() when implemented
            raise NotImplementedError(
                "Live Instagram trend source is not implemented yet. "
                "Use the KnowledgeTrendSource (default) for now."
            )
        return KnowledgeTrendSource()