"""Content post schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    format: str = Field(..., pattern=r"^(story|carousel|reel|live)$")
    title: str | None = Field(None, max_length=255)
    caption: str | None = None
    first_comment: str | None = None
    media_urls: list[str] | None = None
    hashtags: list[str] | None = None
    scheduled_for: datetime | None = None


class PostUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    caption: str | None = None
    first_comment: str | None = None
    media_urls: list[str] | None = None
    hashtags: list[str] | None = None
    format: str | None = Field(None, pattern=r"^(story|carousel|reel|live)?$")
    status: str | None = Field(None, pattern=r"^(draft|scheduled|published|failed)?$")
    scheduled_for: datetime | None = None


class PostResponse(BaseModel):
    id: str
    profile_id: str
    ig_account_id: str | None = None
    format: str
    title: str | None = None
    caption: str | None = None
    first_comment: str | None = None
    media_urls: list[str] | None = None
    hashtags: list[str] | None = None
    status: str
    scheduled_for: datetime | None = None
    published_at: datetime | None = None
    platform_post_id: str | None = None
    platform_permalink: str | None = None
    failure_reason: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
