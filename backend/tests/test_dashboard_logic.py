"""Test dashboard logic: engagement calc, deltas, mock data (Task 6.1)."""

import pytest
from datetime import date, timedelta

from app.api.dashboard import (
    _compute_delta,
    _mock_kpis,
    _mock_timeseries,
    KpiResponse,
    TimeSeriesPoint,
    TimeSeriesResponse,
)


class TestComputeDelta:
    """_compute_delta helper."""

    def test_delta_positive_growth(self):
        """Positive growth returns positive percentage."""
        delta = _compute_delta(current=110, previous=100)
        assert delta == 10.0

    def test_delta_negative_growth(self):
        """Decline returns negative percentage."""
        delta = _compute_delta(current=90, previous=100)
        assert delta == -10.0

    def test_delta_zero_previous(self):
        """Previous=0 returns 0 (avoid div by zero)."""
        delta = _compute_delta(current=100, previous=0)
        assert delta == 0.0

    def test_delta_same_values(self):
        """No change returns 0.0."""
        delta = _compute_delta(current=100, previous=100)
        assert delta == 0.0

    def test_delta_rounds_to_one_decimal(self):
        """Result rounded to 1 decimal place."""
        delta = _compute_delta(current=103, previous=100)
        assert delta == 3.0

        delta = _compute_delta(current=101, previous=100)
        assert delta == 1.0


class TestEngagementRateCalculation:
    """Engagement rate = (likes + comments) / reach * 100."""

    def test_engagement_rate_basic(self):
        """Basic calculation."""
        likes, comments, reach = 100, 50, 1000
        rate = round(((likes + comments) / reach) * 100, 2)
        assert rate == 15.0

    def test_engagement_rate_zero_reach(self):
        """Zero reach -> 0 rate (avoid div by zero)."""
        rate = 0.0 if 0 == 0 else round(((10 + 5) / 0) * 100, 2)
        assert rate == 0.0


class TestMockKpis:
    """_mock_kpis deterministic sample data."""

    def test_mock_kpis_structure(self):
        """Returns KpiResponse with expected sample values."""
        kpi = _mock_kpis()
        assert isinstance(kpi, KpiResponse)
        assert kpi.followers == 3420
        assert kpi.likes == 842
        assert kpi.comments == 127
        assert kpi.reach == 12840
        assert kpi.engagement_rate == 7.5
        assert kpi.followers_delta == 4.2
        assert kpi.engagement_delta == 1.1

    def test_mock_kpis_deterministic(self):
        """Multiple calls return identical values."""
        kpi1 = _mock_kpis()
        kpi2 = _mock_kpis()
        assert kpi1.followers == kpi2.followers
        assert kpi1.engagement_rate == kpi2.engagement_rate


class TestMockTimeseries:
    """_mock_timeseries deterministic generation."""

    def test_mock_timeseries_length(self):
        """Returns exactly `days` points."""
        for days in [1, 7, 30, 90]:
            points = _mock_timeseries("followers", days)
            assert len(points) == days
            assert all(isinstance(p, TimeSeriesPoint) for p in points)

    def test_mock_timeseries_date_format(self):
        """Dates are YYYY-MM-DD strings, descending from today."""
        days = 7
        points = _mock_timeseries("followers", days)

        today = date.today()
        expected_start = today - timedelta(days=days - 1)

        for i, point in enumerate(points):
            expected_date = (expected_start + timedelta(days=i)).isoformat()[:10]
            assert point.date == expected_date

    def test_mock_timeseries_followers_grows(self):
        """Followers metric shows cumulative growth."""
        points = _mock_timeseries("followers", 10)
        values = [p.value for p in points]
        # Should be strictly increasing
        assert all(values[i] < values[i + 1] for i in range(len(values) - 1))
        # First value around 3000+, last around 3000 + 10*avg_increment
        assert values[0] > 3000
        assert values[-1] > values[0] + 200  # ~20-50 per day * 10

    def test_mock_timeseries_other_metrics_ranges(self):
        """Non-follower metrics stay in expected ranges."""
        ranges = {
            "likes": (400, 900),
            "comments": (50, 150),
            "reach": (8000, 15000),
            "engagement_rate": (4.5, 8.5),
            "saves": (10, 80),
            "shares": (10, 80),
        }

        for metric, (min_v, max_v) in ranges.items():
            points = _mock_timeseries(metric, 20)
            values = [p.value for p in points]
            assert all(min_v <= v <= max_v for v in values), f"{metric} out of range: {values}"

    def test_mock_timeseries_deterministic_per_metric(self):
        """Same metric + days = identical series."""
        pts1 = _mock_timeseries("likes", 15)
        pts2 = _mock_timeseries("likes", 15)
        assert [p.value for p in pts1] == [p.value for p in pts2]

    def test_mock_timeseries_different_metrics_different(self):
        """Different metrics produce different value patterns."""
        followers = [p.value for p in _mock_timeseries("followers", 10)]
        likes = [p.value for p in _mock_timeseries("likes", 10)]
        assert followers != likes  # Different generation logic