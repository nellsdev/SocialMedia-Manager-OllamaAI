"""Agent-related schemas for AI content suggestions."""

from pydantic import BaseModel, Field


class CaptionRequest(BaseModel):
    post_context: str = Field(..., min_length=1, description="The post context for caption generation")
    n: int = Field(3, ge=1, le=5, description="Number of caption options")


class CaptionOption(BaseModel):
    text: str
    tone: str = ""
    length: str = ""
    pillar: str = ""


class CaptionResponse(BaseModel):
    options: list[CaptionOption]


class HashtagRequest(BaseModel):
    caption: str = Field(..., min_length=1, description="The post caption")
    pillars: list[str] | None = None


class HashtagResponse(BaseModel):
    hashtags: list[str]


class FormatRequest(BaseModel):
    idea: str = Field(..., min_length=1, description="Content idea description")


class FormatResponse(BaseModel):
    format: str
    reasoning: str = ""


class WeeklyIdeasItem(BaseModel):
    title: str
    description: str = ""
    suggested_format: str = ""
    content_pillar: str = ""


class WeeklyIdeasResponse(BaseModel):
    ideas: list[WeeklyIdeasItem]


class TrendingHashtagsResponse(BaseModel):
    hashtags: list[str]


class TrendingTopicsItem(BaseModel):
    topic: str
    description: str = ""
    relevance: str = ""


class TrendingTopicsResponse(BaseModel):
    topics: list[TrendingTopicsItem]


class ScheduleRequest(BaseModel):
    scheduled_for: str = Field(..., description="ISO 8601 datetime string")


class ScheduleResponse(BaseModel):
    status: str
    job_id: str | None = None


class PublishResponse(BaseModel):
    status: str
    platform_post_id: str | None = None
    platform_permalink: str | None = None
    failure_reason: str | None = None


class OnboardingTurn(BaseModel):
    role: str
    content: str


class OnboardingTurnRequest(BaseModel):
    history: list[OnboardingTurn]
    current_state: str = Field(..., description="One of the onboarding states")
    niche: str | None = None
    archetype: str | None = None


class OnboardingTurnResponse(BaseModel):
    question: str


class OnboardingFinishRequest(BaseModel):
    history: list[OnboardingTurn]


class OnboardingFinishResponse(BaseModel):
    profile: dict
    niche_analysis: dict
