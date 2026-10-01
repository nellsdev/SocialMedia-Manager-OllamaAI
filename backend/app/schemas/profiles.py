"""Profile and strategy schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ProfileResponse(BaseModel):
    id: str
    user_id: str
    name: str
    slug: str
    avatar_url: str | None = None
    archetype: str
    voice_description: str | None = None
    content_pillars: list[str] | None = None
    target_audience: str | None = None
    goals: str | None = None
    visual_references: list[str] | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class StrategyUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    archetype: str | None = None
    voice_description: str | None = None
    content_pillars: list[str] | None = Field(None, max_length=5)
    target_audience: str | None = None
    goals: str | None = None
    visual_references: list[str] | None = None


class ArchetypeResponse(BaseModel):
    id: str
    name: str
    description: str
    default_tone: str
    primary_metric: str
    strategy_focus: str


ARCHETYPES: list[ArchetypeResponse] = [
    ArchetypeResponse(
        id="aspiring_influencer",
        name="Aspiring Influencer",
        description="Growing an audience and attracting brand collaborations",
        default_tone="Trend-aware, engaging",
        primary_metric="Follower growth, reach",
        strategy_focus="Viral hooks, collaborations",
    ),
    ArchetypeResponse(
        id="authority_professional",
        name="Authority Professional",
        description="Building credibility and thought leadership",
        default_tone="Expert, educational",
        primary_metric="Engagement quality",
        strategy_focus="Thought leadership, insights",
    ),
    ArchetypeResponse(
        id="personal_sharing",
        name="Personal Sharing",
        description="Connecting with a close audience authentically",
        default_tone="Warm, authentic",
        primary_metric="Comments, interactions",
        strategy_focus="Lifestyle, everyday moments",
    ),
    ArchetypeResponse(
        id="business_owner",
        name="Business Owner",
        description="Driving sales and leads through content",
        default_tone="Value-first, CTA-oriented",
        primary_metric="Clicks, conversions",
        strategy_focus="Product demos, offers",
    ),
    ArchetypeResponse(
        id="community_builder",
        name="Community Builder",
        description="Engaging a collective around shared interests",
        default_tone="Inclusive, conversational",
        primary_metric="Participation rate",
        strategy_focus="Polls, discussions, UGC",
    ),
]
