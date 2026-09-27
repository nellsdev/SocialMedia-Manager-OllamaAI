"""Agent memory abstraction — dual backend (Engram for dev, Supabase for prod).

Engram (local SQLite) is used during development for agent introspection
and prompt debugging. Supabase PostgreSQL is used in production with
RLS scoped per profile.

Usage:
    memory = get_agent_memory()
    await memory.save_interaction(
        profile_id="uuid",
        agent_type="content_creator",
        task="weekly-ideas",
        prompt="...",
        response="...",
    )
    history = await memory.get_recent_interactions(
        profile_id="uuid", agent_type="content_creator", limit=5
    )
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class AgentInteraction:
    id: str | None = None
    profile_id: str | None = None
    agent_type: str = ""
    task: str = ""
    prompt: str = ""
    response: str = ""
    model: str = ""
    latency_ms: int | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------

class AgentMemory(ABC):
    """Backend-agnostic agent memory store."""

    @abstractmethod
    async def save_interaction(self, interaction: AgentInteraction) -> str | None:
        """Persist an interaction. Returns the interaction id or None."""
        ...

    @abstractmethod
    async def get_recent_interactions(
        self,
        profile_id: str,
        agent_type: str | None = None,
        task: str | None = None,
        limit: int = 10,
    ) -> list[AgentInteraction]:
        """Fetch recent interactions for a profile, optionally filtered."""
        ...

    @abstractmethod
    async def get_profile_context(self, profile_id: str) -> dict[str, Any]:
        """Return aggregated memory context for a profile (e.g. recent themes)."""
        ...


# ---------------------------------------------------------------------------
# Engram backend (development / local)
# ---------------------------------------------------------------------------

class EngramMemory(AgentMemory):
    """Uses the local Engram CLI for lightweight dev memory.

    Observations are saved with type='agent_interaction' and tagged with
    the profile_id in the message so they remain searchable.
    """

    def __init__(self, project: str = "social-media-manager") -> None:
        self.project = project

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["engram", *args, "--project", self.project],
            capture_output=True,
            text=True,
            check=False,
        )

    async def save_interaction(self, interaction: AgentInteraction) -> str | None:
        try:
            payload = {
                "profile_id": interaction.profile_id,
                "agent_type": interaction.agent_type,
                "task": interaction.task,
                "model": interaction.model,
                "latency_ms": interaction.latency_ms,
                "metadata": interaction.metadata or {},
            }
            # We split prompt/response into title + body because Engram
            # observations have a title and a message field.
            title = f"[{interaction.agent_type}/{interaction.task}] {interaction.prompt[:60]}..."
            message = (
                f"**Prompt:**\n{interaction.prompt}\n\n"
                f"**Response:**\n{interaction.response}\n\n"
                f"**Meta:** {json.dumps(payload, ensure_ascii=False)}"
            )
            result = self._run(
                "save", title, message,
                "--type", "agent_interaction",
                "--scope", "project",
            )
            if result.returncode != 0:
                logger.warning("Engram save failed: %s", result.stderr)
                return None
            # Engram prints something like "Saved observation #123"
            # We don't have an easy way to parse the id, so return a pseudo-id.
            return f"engram:{interaction.profile_id}:{datetime.now(timezone.utc).isoformat()}"
        except Exception as exc:
            logger.warning("Engram save exception: %s", exc)
            return None

    async def get_recent_interactions(
        self,
        profile_id: str,
        agent_type: str | None = None,
        task: str | None = None,
        limit: int = 10,
    ) -> list[AgentInteraction]:
        try:
            query_parts = [f"profile_id:{profile_id}"]
            if agent_type:
                query_parts.append(f"agent_type:{agent_type}")
            if task:
                query_parts.append(f"task:{task}")
            query = " ".join(query_parts)

            result = self._run(
                "search", query,
                "--type", "agent_interaction",
                "--limit", str(limit),
            )
            if result.returncode != 0:
                logger.debug("Engram search failed: %s", result.stderr)
                return []

            interactions: list[AgentInteraction] = []
            # Engram search output is human-readable; best-effort parsing.
            # Each result starts with "[N] #<id> ..."
            for line in result.stdout.splitlines():
                if line.strip().startswith("[") and "agent_interaction" in line:
                    interactions.append(
                        AgentInteraction(
                            profile_id=profile_id,
                            agent_type=agent_type or "unknown",
                            task=task or "unknown",
                            response=line,
                        )
                    )
            return interactions
        except Exception as exc:
            logger.warning("Engram search exception: %s", exc)
            return []

    async def get_profile_context(self, profile_id: str) -> dict[str, Any]:
        """Dev fallback — returns empty context."""
        return {}


# ---------------------------------------------------------------------------
# Supabase backend (production)
# ---------------------------------------------------------------------------

class SupabaseMemory(AgentMemory):
    """Uses the Supabase PostgreSQL table `agent_memories`.

    Table schema (add via migration):
        CREATE TABLE agent_memories (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
            agent_type TEXT NOT NULL,
            task TEXT NOT NULL,
            prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            model TEXT,
            latency_ms INTEGER,
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX idx_agent_memories_profile ON agent_memories(profile_id, created_at DESC);
        CREATE INDEX idx_agent_memories_agent ON agent_memories(profile_id, agent_type, created_at DESC);

        ALTER TABLE agent_memories ENABLE ROW LEVEL SECURITY;
        CREATE POLICY "own_agent_memories" ON agent_memories
            FOR ALL USING (profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));
    """

    def __init__(self) -> None:
        # Lazy import to avoid circular deps and Supabase init at import time
        self._supabase = None

    def _client(self):
        if self._supabase is None:
            from app.core.database import get_supabase_service_client
            self._supabase = get_supabase_service_client()
        return self._supabase

    async def save_interaction(self, interaction: AgentInteraction) -> str | None:
        try:
            data = {
                "profile_id": interaction.profile_id,
                "agent_type": interaction.agent_type,
                "task": interaction.task,
                "prompt": interaction.prompt,
                "response": interaction.response,
                "model": interaction.model,
                "latency_ms": interaction.latency_ms,
                "metadata": interaction.metadata or {},
            }
            resp = self._client().table("agent_memories").insert(data).execute()
            if resp.data and len(resp.data) > 0:
                return resp.data[0].get("id")
            return None
        except Exception as exc:
            logger.warning("Supabase memory save failed: %s", exc)
            return None

    async def get_recent_interactions(
        self,
        profile_id: str,
        agent_type: str | None = None,
        task: str | None = None,
        limit: int = 10,
    ) -> list[AgentInteraction]:
        try:
            query = (
                self._client()
                .table("agent_memories")
                .select("*")
                .eq("profile_id", profile_id)
                .order("created_at", desc=True)
                .limit(limit)
            )
            if agent_type:
                query = query.eq("agent_type", agent_type)
            if task:
                query = query.eq("task", task)
            resp = query.execute()
            return [self._to_interaction(row) for row in (resp.data or [])]
        except Exception as exc:
            logger.warning("Supabase memory fetch failed: %s", exc)
            return []

    async def get_profile_context(self, profile_id: str) -> dict[str, Any]:
        """Aggregate recent themes from stored interactions."""
        try:
            resp = (
                self._client()
                .table("agent_memories")
                .select("task, agent_type")
                .eq("profile_id", profile_id)
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            )
            rows = resp.data or []
            task_counts: dict[str, int] = {}
            agent_counts: dict[str, int] = {}
            for row in rows:
                task_counts[row.get("task", "unknown")] = task_counts.get(row.get("task"), 0) + 1
                agent_counts[row.get("agent_type", "unknown")] = agent_counts.get(row.get("agent_type"), 0) + 1
            return {
                "total_interactions": len(rows),
                "top_tasks": sorted(task_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                "top_agents": sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            }
        except Exception as exc:
            logger.warning("Supabase context aggregation failed: %s", exc)
            return {}

    @staticmethod
    def _to_interaction(row: dict[str, Any]) -> AgentInteraction:
        return AgentInteraction(
            id=row.get("id"),
            profile_id=row.get("profile_id"),
            agent_type=row.get("agent_type", ""),
            task=row.get("task", ""),
            prompt=row.get("prompt", ""),
            response=row.get("response", ""),
            model=row.get("model", ""),
            latency_ms=row.get("latency_ms"),
            created_at=row.get("created_at"),
            metadata=row.get("metadata"),
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_MEMORY_INSTANCE: AgentMemory | None = None


def get_agent_memory() -> AgentMemory:
    """Return the singleton memory backend.

    Uses Engram when ``AGENT_MEMORY_BACKEND=engram`` (default in dev),
    otherwise falls back to Supabase.
    """
    global _MEMORY_INSTANCE
    if _MEMORY_INSTANCE is None:
        backend = os.getenv("AGENT_MEMORY_BACKEND", "supabase").lower()
        if backend == "engram":
            _MEMORY_INSTANCE = EngramMemory()
            logger.info("Agent memory: Engram (dev)")
        else:
            _MEMORY_INSTANCE = SupabaseMemory()
            logger.info("Agent memory: Supabase (prod)")
    return _MEMORY_INSTANCE


def reset_agent_memory() -> None:
    """Reset the singleton (useful in tests)."""
    global _MEMORY_INSTANCE
    _MEMORY_INSTANCE = None
