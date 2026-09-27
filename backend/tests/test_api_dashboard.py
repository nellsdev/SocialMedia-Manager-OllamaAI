"""Test API routes: Dashboard endpoints with mocked Supabase (Task 6.2)."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock


class TestDashboardKpis:
    """GET /api/dashboard/kpis"""

    def test_kpis_returns_mock_when_debug_and_no_db(self, client):
        """DEBUG=true + no Supabase -> returns mock KPIs (not 500)."""
        response = client.get("/api/dashboard/kpis")
        assert response.status_code == 200

        data = response.json()
        assert data["followers"] == 3420
        assert data["likes"] == 842
        assert data["comments"] == 127
        assert data["reach"] == 12840
        assert data["engagement_rate"] == 7.5
        assert "followers_delta" in data
        assert "engagement_delta" in data

    def test_kpis_response_shape(self, client):
        """Response matches KpiResponse schema."""
        response = client.get("/api/dashboard/kpis")
        data = response.json()

        expected_keys = {
            "followers", "likes", "comments", "reach",
            "engagement_rate", "followers_delta", "engagement_delta"
        }
        assert set(data.keys()) == expected_keys
        assert all(isinstance(data[k], (int, float)) for k in data)


class TestDashboardTimeseries:
    """GET /api/dashboard/timeseries"""

    def test_timeseries_default_params(self, client):
        """Default metric=followers, days=30 returns mock series."""
        response = client.get("/api/dashboard/timeseries")
        assert response.status_code == 200

        data = response.json()
        assert data["metric"] == "followers"
        assert data["days"] == 30
        assert len(data["data"]) == 30
        assert all("date" in p and "value" in p for p in data["data"])

    def test_timeseries_custom_metric(self, client):
        """Custom metric parameter works."""
        for metric in ["followers", "likes", "comments", "reach", "engagement_rate", "saves", "shares"]:
            response = client.get(f"/api/dashboard/timeseries?metric={metric}")
            assert response.status_code == 200
            data = response.json()
            assert data["metric"] == metric
            assert len(data["data"]) == 30  # default days

    def test_timeseries_custom_days(self, client):
        """Custom days parameter works (1-90)."""
        for days in [1, 7, 30, 90]:
            response = client.get(f"/api/dashboard/timeseries?metric=followers&days={days}")
            assert response.status_code == 200
            data = response.json()
            assert data["days"] == days
            assert len(data["data"]) == days

    def test_timeseries_invalid_metric_returns_400(self, client):
        """Invalid metric returns 400 with helpful message."""
        response = client.get("/api/dashboard/timeseries?metric=invalid_metric")
        assert response.status_code == 400
        error = response.json()
        assert "detail" in error
        assert "invalid" in error["detail"].lower()

    def test_timeseries_days_out_of_bounds(self, client):
        """days < 1 or > 90 returns 422 (FastAPI validation)."""
        response = client.get("/api/dashboard/timeseries?days=0")
        assert response.status_code == 422

        response = client.get("/api/dashboard/timeseries?days=91")
        assert response.status_code == 422

    def test_timeseries_date_order_ascending(self, client):
        """Dates returned in ascending order (oldest first)."""
        response = client.get("/api/dashboard/timeseries?metric=followers&days=7")
        data = response.json()

        dates = [p["date"] for p in data["data"]]
        assert dates == sorted(dates)  # ascending

    def test_timeseries_values_are_numbers(self, client):
        """All values are numeric (int/float)."""
        response = client.get("/api/dashboard/timeseries?metric=engagement_rate&days=5")
        data = response.json()

        for point in data["data"]:
            assert isinstance(point["value"], (int, float))


class TestDashboardAuthBehavior:
    """Auth behavior notes (currently mocked in DEBUG)."""

    def test_kpis_does_not_require_explicit_auth_in_debug(self, client):
        """In DEBUG mode, endpoint doesn't require auth header (mock bypasses)."""
        # No Authorization header sent
        response = client.get("/api/dashboard/kpis")
        assert response.status_code == 200  # mock kicks in