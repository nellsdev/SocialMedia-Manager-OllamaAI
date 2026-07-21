"""Analytics Agent (3.5).

Fetches Instagram metrics and computes engagement KPIs. For the MVP this
agent provides computed engagement rates and mock data; real Instagram
Graph API integration for fetching actual metrics will come after platform
review approval.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class MetricsSnapshot:
    metric_date: date | str
    followers: int = 0
    likes: int = 0
    comments: int = 0
    reach: int = 0
    saves: int = 0
    shares: int = 0
    engagement_rate: float = 0.0
    raw_data: dict | None = None


class AnalyticsAgent(BaseAgent):
    """Fetches Instagram metrics and computes engagement KPIs."""

    async def fetch_metrics(self, account_id: str) -> MetricsSnapshot:
        """Fetch the latest metrics for the given IG account.

        For MVP this returns computed mock data. Production will call the
        Instagram Graph API ``/{ig-user-id}/insights`` endpoint.
        """
        # TODO: Replace with real Instagram Graph API call after app review
        logger.warning("AnalyticsAgent.fetch_metrics uses mock data (no IG API token yet)")
        return MetricsSnapshot(
            metric_date=date.today().isoformat(),
            followers=0,
            likes=0,
            comments=0,
            reach=0,
            saves=0,
            shares=0,
            engagement_rate=0.0,
        )

    async def get_timeseries(self, days: int = 30) -> list[MetricsSnapshot]:
        """Return a time series of metrics over *days*.

        For MVP this returns a list of empty snapshots. Real integration
        will read from the metrics_snapshots table.
        """
        today = date.today()
        return [
            MetricsSnapshot(
                metric_date=(today - timedelta(days=d)).isoformat(),
            )
            for d in range(days, 0, -1)
        ]

    async def compute_engagement_rate(
        self,
        likes: int,
        comments: int,
        reach: int,
    ) -> float:
        """Compute engagement rate as (likes + comments) / reach * 100.

        Returns 0.0 when reach is zero to avoid division by zero.
        """
        if reach <= 0:
            return 0.0
        return round(((likes + comments) / reach) * 100, 2)

    async def run(self, **kwargs) -> object:
        task = kwargs.get("task", "fetch")
        if task == "fetch":
            return await self.fetch_metrics(
                account_id=kwargs.get("account_id", ""),
            )
        if task == "timeseries":
            return await self.get_timeseries(
                days=kwargs.get("days", 30),
            )
        if task == "engagement-rate":
            return await self.compute_engagement_rate(
                likes=kwargs.get("likes", 0),
                comments=kwargs.get("comments", 0),
                reach=kwargs.get("reach", 0),
            )
        raise ValueError(f"Unknown task: {task}")
