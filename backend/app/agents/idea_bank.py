"""Idea Bank Agent (3.7).

Processes incoming ideas from WhatsApp and manual entry. Provides
auto-tagging (pillar classification) and format recommendations using
the **phi4-mini:3.8b** model via Ollama for structured classification.
"""

import json
import logging
from dataclasses import dataclass

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class Idea:
    title: str
    description: str = ""
    suggested_format: str | None = None
    content_pillar: str | None = None
    source: str = "manual"
    media_refs: list[str] | None = None


@dataclass
class FormatRecommendation:
    format: str  # story / carousel / reel / live
    reasoning: str = ""


class IdeaBankAgent(BaseAgent):
    """Processes incoming ideas, auto-categorises, and suggests formats.

    Uses **phi4-mini:3.8b** via Ollama for lightweight classification tasks
    (pillar tagging, format recommendation).
    """

    MODEL = "phi4-mini:3.8b"
    OLLAMA_BASE_URL = "http://localhost:11434"

    async def process_whatsapp_message(
        self,
        text: str,
        media: list[str] | None = None,
    ) -> Idea:
        """Process an incoming WhatsApp message into a structured Idea.

        Performs auto-tagging and format suggestion on the message text.
        """
        pillar = await self.auto_tag_pillar(text)
        format_rec = await self.suggest_format_from_text(text)

        # Use the first line or first 80 chars as title
        title = text.strip().split("\n")[0][:80] if text.strip() else "WhatsApp Idea"

        return Idea(
            title=title,
            description=text,
            suggested_format=format_rec.format if format_rec else None,
            content_pillar=pillar,
            source="whatsapp",
            media_refs=media or [],
        )

    async def auto_tag_pillar(self, description: str) -> str | None:
        """Classify a description into one of the profile's content pillars.

        Returns the pillar name or ``None`` if it cannot be classified.
        If the profile has defined pillars, the classification is scoped
        to those values.
        """
        valid_pillars = self._profile.content_pillars if self._profile and self._profile.content_pillars else None
        prompt = self._build_pillar_prompt(description, valid_pillars)
        raw = await self._ollama_generate(prompt)
        return self._parse_pillar(raw, valid_pillars)

    async def suggest_format_from_text(self, description: str) -> FormatRecommendation | None:
        """Suggest an Instagram format based on the description text."""
        prompt = self._build_format_prompt(description)
        raw = await self._ollama_generate(prompt)
        return self._parse_format(raw)

    async def run(self, **kwargs) -> object:
        task = kwargs.get("task", "whatsapp")
        if task == "whatsapp":
            return await self.process_whatsapp_message(
                text=kwargs.get("text", ""),
                media=kwargs.get("media"),
            )
        if task == "auto-tag":
            return await self.auto_tag_pillar(
                description=kwargs.get("description", ""),
            )
        if task == "suggest-format":
            return await self.suggest_format_from_text(
                description=kwargs.get("description", ""),
            )
        raise ValueError(f"Unknown task: {task}")

    def _build_pillar_prompt(self, description: str, valid_pillars: list[str] | None) -> str:
        parts = [
            "You are a content classification assistant. Your job is to classify the following "
            "content description into one content pillar.",
        ]
        if valid_pillars:
            parts.append(f"Valid pillars: {', '.join(valid_pillars)}")
        else:
            parts.append("If none apply, return 'general'.")
        parts.append("")
        parts.append(f"Description: {description}")
        parts.append("")
        parts.append(
            "Return ONLY a JSON object with a single key 'pillar' containing the pillar name as a string. "
            "No markdown, no explanation."
        )
        return "\n".join(parts)

    def _build_format_prompt(self, description: str) -> str:
        parts = [
            "You are an Instagram format advisor.",
            f"Content description: {description}",
            "",
            "Based on the content type, recommend one Instagram format: story, carousel, reel, or live. "
            'Return ONLY a JSON object with keys "format" and "reasoning". '
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
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                }
                resp = await client.post(
                    f"{self.OLLAMA_BASE_URL}/api/generate",
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

    def _parse_pillar(self, raw: str, valid_pillars: list[str] | None) -> str | None:
        cleaned = self._clean_json(raw)
        try:
            data = json.loads(cleaned)
            pillar = data.get("pillar", "").strip()
            if not pillar:
                return None
            if valid_pillars and pillar not in valid_pillars:
                return None
            return pillar
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to parse pillar: %s — raw: %s", exc, raw[:200])
            # Fallback: check if raw is just a simple word
            cleaned_text = raw.strip().strip('"').strip("'")
            if cleaned_text and len(cleaned_text) < 100 and " " not in cleaned_text:
                return cleaned_text
            return None

    def _parse_format(self, raw: str) -> FormatRecommendation | None:
        cleaned = self._clean_json(raw)
        try:
            data = json.loads(cleaned)
            fmt = data.get("format", "").strip().lower()
            if fmt not in ("story", "carousel", "reel", "live"):
                return None
            return FormatRecommendation(
                format=fmt,
                reasoning=data.get("reasoning", ""),
            )
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to parse format: %s — raw: %s", exc, raw[:200])
            return None
