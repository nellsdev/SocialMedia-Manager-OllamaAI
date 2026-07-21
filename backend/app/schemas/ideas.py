"""Content idea schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class IdeaCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    suggested_format: str | None = Field(None, pattern=r"^(story|carousel|reel|live)?$")
    content_pillar: str | None = None


class IdeaResponse(BaseModel):
    id: str
    profile_id: str
    title: str
    description: str | None = None
    suggested_format: str | None = None
    content_pillar: str | None = None
    source: str
    media_refs: list[str] | None = None
    status: str
    converted_to: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class IdeaConvertResponse(BaseModel):
    post_id: str
    message: str = "Idea converted to draft post"
