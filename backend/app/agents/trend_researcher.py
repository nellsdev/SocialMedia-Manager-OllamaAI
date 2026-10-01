"""Trend Researcher Agent (3.4).

Provides trending hashtags and topic suggestions based on the profile's
content pillars. Uses the **qwen2.5:7b** model via Ollama for trend-aware
recommendations.

For a single-user MVP this agent relies on the LLM's training knowledge
rather than live Instagram API scraping. Future versions can integrate the
Instagram Graph API hashtag search endpoint.
"""

import json
import logging
from dataclasses import dataclass

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class TrendTopic:
    topic: str
    description: str = ""
    relevance: str = ""  # high / medium / low


class TrendResearcherAgent(BaseAgent):
    """Fetches trending hashtags and topics relevant to the profile's pillars."""

    MODEL = "qwen2.5:7b"

    async def get_trending_hashtags(self, pillars: list[str] | None = None) -> list[str]:
        """Return trending hashtags for the given content pillars."""
        prompt = self._build_trending_hashtag_prompt(pillars)
        raw = await self._ollama_generate(prompt)
        return self._parse_list(raw)

    async def get_trending_topics(self, niche: str) -> list[TrendTopic]:
        """Return trending topic ideas for a given niche."""
        prompt = self._build_trending_topics_prompt(niche)
        raw = await self._ollama_generate(prompt)
        return self._parse_topics(raw)

    async def analyze_niche(self, niche: str, reference_accounts: list[str] | None = None) -> dict:
        """Produce a full strategic niche analysis (dict for JSON persistence).

        Delegates to the configured TrendDataSource (knowledge-based for MVP,
        swappable for live Instagram data later via TrendDataSourceFactory).
        """
        from app.core.trend_data_source import TrendDataSourceFactory

        source = TrendDataSourceFactory.get()
        analysis = await source.analyze_reference_accounts(
            niche, reference_accounts or []
        )
        return analysis.to_dict()

    async def run(self, **kwargs) -> object:
        task = kwargs.get("task", "hashtags")
        if task == "hashtags":
            return await self.get_trending_hashtags(
                pillars=kwargs.get("pillars"),
            )
        if task == "topics":
            return await self.get_trending_topics(
                niche=kwargs.get("niche", ""),
            )
        if task == "analyze-niche":
            return await self.analyze_niche(
                niche=kwargs.get("niche", ""),
                reference_accounts=kwargs.get("reference_accounts"),
            )
        raise ValueError(f"Unknown task: {task}")

    def _build_trending_hashtag_prompt(self, pillars: list[str] | None) -> str:
        parts = [
            "You are an Instagram trend analyst. Suggest trending hashtags for the following content pillars.",
        ]
        if pillars:
            parts.append(f"Content pillars: {', '.join(pillars)}")
        parts.append("")
        parts.append(
            "Return ONLY a JSON array of strings (hashtags without the # symbol). "
            "No markdown, no explanation."
        )
        return "\n".join(parts)

    def _build_trending_topics_prompt(self, niche: str) -> str:
        parts = [
            f"You are a social media trend researcher focused on the niche: {niche}.",
            "",
            "Suggest 5 currently relevant trending topics or content angles. "
            'Return ONLY a JSON array of objects with keys "topic", "description", and "relevance" (high/medium/low). '
            "No markdown, no explanation.",
        ]
        return "\n".join(parts)

    async def _ollama_generate(self, prompt: str) -> str:
        """Send a prompt to Ollama and return the raw response text.

        Retries up to 3 times with exponential backoff on transient errors.
        """
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

    def _parse_list(self, raw: str) -> list[str]:
        cleaned = self._clean_json(raw)
        try:
            items = json.loads(cleaned)
            return [h.lstrip("#") for h in (items or []) if isinstance(h, str) and h.strip()][:10]
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to parse trend list: %s — raw: %s", exc, raw[:200])
            import re

            return re.findall(r"(\w+)", raw)[:10]

    def _parse_topics(self, raw: str) -> list[TrendTopic]:
        cleaned = self._clean_json(raw)
        try:
            items = json.loads(cleaned)
            if isinstance(items, dict):
                items = [items]
            return [
                TrendTopic(
                    topic=item.get("topic", ""),
                    description=item.get("description", ""),
                    relevance=item.get("relevance", "medium"),
                )
                for item in (items or [])
                if item.get("topic")
            ][:5]
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to parse topics: %s — raw: %s", exc, raw[:200])
            return [TrendTopic(topic=raw.strip())]
