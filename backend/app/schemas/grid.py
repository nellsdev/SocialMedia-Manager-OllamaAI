"""Content grid / calendar schemas."""

from datetime import date

from pydantic import BaseModel

from app.schemas.posts import PostResponse


class GridDay(BaseModel):
    date: date
    posts: list[PostResponse] = []


class GridResponse(BaseModel):
    year: int
    month: int
    days: list[GridDay] = []


class PillarBreakdown(BaseModel):
    name: str
    count: int
    percentage: float


class FormatBreakdown(BaseModel):
    name: str
    count: int
    percentage: float


class GridDistributionResponse(BaseModel):
    pillars: list[PillarBreakdown] = []
    formats: list[FormatBreakdown] = []
    total_posts: int = 0
