"""Abstract base agent for the multi-agent system (3.1).

All agents inherit from BaseAgent. The profile attribute provides strategy
context (archetype, voice, content pillars, audience, goals) that every agent
needs to personalise its output.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProfileStrategy:
    """Strategy profile context injected into every agent."""

    profile_id: str
    archetype: str  # aspiring_influencer, authority_professional, personal_sharing, business_owner, community_builder
    voice_description: str | None = None
    content_pillars: list[str] | None = None
    target_audience: str | None = None
    goals: str | None = None
    visual_references: list[str] | None = None


class BaseAgent(ABC):
    """Abstract base agent that all specialised agents extend.

    Each agent holds a reference to the user's strategy profile so every
    suggestion is tailored to the creator's archetype, voice, and pillars.
    """

    def __init__(self, profile: ProfileStrategy | None = None) -> None:
        self._profile = profile

    # ------------------------------------------------------------------
    # Public profile accessors
    # ------------------------------------------------------------------

    @property
    def profile(self) -> ProfileStrategy | None:
        return self._profile

    @profile.setter
    def profile(self, value: ProfileStrategy | None) -> None:
        self._profile = value

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def run(self, **kwargs) -> object:
        """Execute the agent's primary task.

        Subclasses MUST implement this. The keyword arguments are specific
        to each agent type.
        """
        ...
