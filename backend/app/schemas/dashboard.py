"""Dashboard schemas — KPIs and time series."""

from pydantic import BaseModel, Field


class KpiResponse(BaseModel):
    followers: int = 0
    likes: int = 0
    comments: int = 0
    reach: int = 0
    engagement_rate: float = 0.0
    followers_delta: float = 0.0
    engagement_delta: float = 0.0


class TimeSeriesPoint(BaseModel):
    date: str
    value: float


class TimeSeriesResponse(BaseModel):
    metric: str
    days: int
    data: list[TimeSeriesPoint] = Field(default_factory=list)
