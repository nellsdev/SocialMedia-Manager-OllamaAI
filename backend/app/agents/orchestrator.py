"""Orchestrator Agent (3.2).

Coordinates the multi-agent system. Routes tasks to the appropriate
specialised agent based on task type. Uses **phi4-mini:3.8b** via Ollama
for lightweight routing decisions when the task type is ambiguous.

The Orchestrator owns agent lifecycle — agents are lazily created and
cached after first use.
"""

import enum
import logging
from dataclasses import dataclass

from app.agents.base import BaseAgent, ProfileStrategy
from app.agents.content_creator import ContentCreatorAgent
from app.agents.trend_researcher import TrendResearcherAgent
from app.agents.analytics_agent import AnalyticsAgent
from app.agents.scheduler_agent import SchedulerAgent
from app.agents.idea_bank import IdeaBankAgent

logger = logging.getLogger(__name__)


class AgentType(str, enum.Enum):
    CONTENT_CREATOR = "content_creator"
    TREND_RESEARCHER = "trend_researcher"
    ANALYTICS = "analytics"
    SCHEDULER = "scheduler"
    IDEA_BANK = "idea_bank"


@dataclass
class AgentTask:
    task_type: str  # e.g. "captions", "hashtags", "schedule", "whatsapp"
    params: dict  # kwargs to pass to the agent
    profile_id: str | None = None


@dataclass
class AgentResult:
    agent_type: AgentType | str
    task: str
    data: object
    error: str | None = None


class Orchestrator:
    """Orchestrator coordinator.

    Routes tasks to the appropriate agent based on task type and profile.
    Agents are lazily instantiated and cached.
    """

    # Mapping of task type to agent class
    TASK_ROUTES: dict[str, AgentType] = {
        "captions": AgentType.CONTENT_CREATOR,
        "hashtags": AgentType.CONTENT_CREATOR,
        "format": AgentType.CONTENT_CREATOR,
        "weekly-ideas": AgentType.CONTENT_CREATOR,
        "trending-hashtags": AgentType.TREND_RESEARCHER,
        "trending-topics": AgentType.TREND_RESEARCHER,
        "fetch-metrics": AgentType.ANALYTICS,
        "timeseries": AgentType.ANALYTICS,
        "engagement-rate": AgentType.ANALYTICS,
        "schedule": AgentType.SCHEDULER,
        "cancel": AgentType.SCHEDULER,
        "publish": AgentType.SCHEDULER,
        "retry": AgentType.SCHEDULER,
        "whatsapp": AgentType.IDEA_BANK,
        "auto-tag": AgentType.IDEA_BANK,
        "suggest-format": AgentType.IDEA_BANK,
    }

    def __init__(self) -> None:
        self._agents: dict[AgentType, BaseAgent] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_task(self, task: AgentTask) -> AgentResult:
        """Route a single task to the appropriate agent and return the result."""
        agent = await self.get_agent_for_task(task)
        try:
            params = {**task.params, "task": task.task_type}
            data = await agent.run(**params)
            return AgentResult(
                agent_type=agent.__class__.__name__,
                task=task.task_type,
                data=data,
            )
        except Exception as exc:
            logger.exception("Agent task %s failed", task.task_type)
            return AgentResult(
                agent_type=agent.__class__.__name__,
                task=task.task_type,
                data=None,
                error=str(exc),
            )

    async def run_batch(self, tasks: list[AgentTask]) -> list[AgentResult]:
        """Execute multiple tasks concurrently."""
        import asyncio

        return await asyncio.gather(
            *(self.run_task(t) for t in tasks),
        )

    async def get_agent(self, agent_type: AgentType) -> BaseAgent:
        """Return the cached agent for the given type, creating it if needed."""
        if agent_type not in self._agents:
            self._agents[agent_type] = self._create_agent(agent_type)
        return self._agents[agent_type]

    def set_profile(self, profile: ProfileStrategy) -> None:
        """Update the profile context on all created agents."""
        for agent in self._agents.values():
            agent.profile = profile

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def get_agent_for_task(self, task: AgentTask) -> BaseAgent:
        """Determine the correct agent for a task and set its profile."""
        agent_type = self.TASK_ROUTES.get(task.task_type)
        if agent_type is None:
            # Fallback: use routing via phi4-mini if task type is unknown
            agent_type = await self._route_task_type(task.task_type)

        agent = await self.get_agent(agent_type)

        # If profile_id is provided, try to load and set the profile
        if task.profile_id:
            try:
                profile = await self._load_profile(task.profile_id)
                if profile:
                    agent.profile = profile
            except Exception as exc:
                logger.warning("Could not load profile %s: %s", task.profile_id, exc)

        return agent

    def _create_agent(self, agent_type: AgentType) -> BaseAgent:
        """Factory method — creates a new agent of the given type."""
        mapping = {
            AgentType.CONTENT_CREATOR: ContentCreatorAgent,
            AgentType.TREND_RESEARCHER: TrendResearcherAgent,
            AgentType.ANALYTICS: AnalyticsAgent,
            AgentType.SCHEDULER: SchedulerAgent,
            AgentType.IDEA_BANK: IdeaBankAgent,
        }
        cls = mapping.get(agent_type)
        if not cls:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return cls()

    async def _route_task_type(self, task_type: str) -> AgentType:
        """Use phi4-mini to route an unknown task type to an agent.

        Falls back to ContentCreatorAgent if routing fails.
        """
        try:
            import httpx

            prompt = (
                f"Map the following task to one of these agent types: "
                f"content_creator, trend_researcher, analytics, scheduler, idea_bank.\n\n"
                f"Task: {task_type}\n\n"
                f"Return ONLY a single word with the agent type. No explanation."
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                from app.core.config import settings
                resp = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={"model": "phi4-mini:3.8b", "prompt": prompt, "stream": False},
                )
                resp.raise_for_status()
                data = resp.json()
                raw_type = data.get("response", "").strip().lower()

                for at in AgentType:
                    if at.value in raw_type:
                        return at

            logger.warning("Could not route task '%s', falling back to content_creator", task_type)
            return AgentType.CONTENT_CREATOR
        except Exception as exc:
            logger.warning("Routing via Ollama failed: %s. Falling back to content_creator.", exc)
            return AgentType.CONTENT_CREATOR

    async def _load_profile(self, profile_id: str) -> ProfileStrategy | None:
        """Load a profile strategy from the database."""
        try:
            from app.core.database import get_supabase_service_client

            supabase = get_supabase_service_client()
            resp = supabase.table("profiles").select("*").eq("id", profile_id).maybe_single().execute()
            if not resp.data:
                return None
            p = resp.data
            return ProfileStrategy(
                profile_id=p["id"],
                archetype=p.get("archetype", "personal_sharing"),
                voice_description=p.get("voice_description"),
                content_pillars=p.get("content_pillars"),
                target_audience=p.get("target_audience"),
                goals=p.get("goals"),
                visual_references=p.get("visual_references"),
            )
        except Exception as exc:
            logger.warning("Could not load profile %s: %s", profile_id, exc)
            return None
