"""Test SchedulerAgent APScheduler job registration and lifecycle (Task 6.4)."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from app.agents.scheduler_agent import (
    SchedulerAgent,
    get_scheduler,
    reconcile_scheduled_jobs,
    _get_scheduler_db_url,
    MAX_RETRIES,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
)


class TestSchedulerSingleton:
    """get_scheduler() singleton behavior."""

    def test_get_scheduler_returns_same_instance(self):
        """Multiple calls return same scheduler instance."""
        with patch("app.agents.scheduler_agent._scheduler", None):
            sched1 = get_scheduler()
            sched2 = get_scheduler()
            assert sched1 is sched2

    def test_scheduler_starts_on_first_call(self):
        """Scheduler starts when first accessed."""
        with patch("app.agents.scheduler_agent._scheduler", None):
            with patch("app.agents.scheduler_agent.SQLAlchemyJobStore") as mock_jobstore:
                with patch("app.agents.scheduler_agent.AsyncIOScheduler") as mock_sched_class:
                    mock_sched = MagicMock()
                    mock_sched.running = True
                    mock_sched_class.return_value = mock_sched

                    sched = get_scheduler()

                    mock_sched_class.assert_called_once()
                    mock_sched.start.assert_called_once()
                    assert sched.running is True


class TestSchedulerDBUrl:
    """_get_scheduler_db_url converts Supabase URL to PostgreSQL."""

    def test_http_url_conversion(self):
        """http:// -> postgresql://"""
        with patch("app.agents.scheduler_agent.settings") as mock_settings:
            mock_settings.SUPABASE_URL = "http://localhost:54321"
            url = _get_scheduler_db_url()
            assert url == "postgresql://localhost:54321"

    def test_https_url_conversion(self):
        """https:// -> postgresql://"""
        with patch("app.agents.scheduler_agent.settings") as mock_settings:
            mock_settings.SUPABASE_URL = "https://db.supabase.co"
            url = _get_scheduler_db_url()
            assert url == "postgresql://db.supabase.co"


class TestReconcileScheduledJobs:
    """reconcile_scheduled_jobs re-registers pending jobs on startup."""

    @pytest.mark.asyncio
    async def test_reconcile_fetches_scheduled_jobs(self):
        """Queries scheduler_jobs with status=scheduled."""
        with patch("app.agents.scheduler_agent.get_supabase_service_client") as mock_get_client:
            mock_supabase = MagicMock()
            mock_get_client.return_value = mock_supabase

            mock_execute = MagicMock()
            mock_execute.data = [
                {"post_id": "post-1", "scheduled_at": "2099-01-01T12:00:00+00:00"},
                {"post_id": "post-2", "scheduled_at": "2099-01-02T12:00:00+00:00"},
            ]
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_execute

            with patch("app.agents.scheduler_agent._scheduler") as mock_sched:
                mock_sched.add_job = MagicMock()

                await reconcile_scheduled_jobs()

                # Should query scheduler_jobs
                mock_supabase.table.assert_called_with("scheduler_jobs")
                # Should add both jobs
                assert mock_sched.add_job.call_count == 2

    @pytest.mark.asyncio
    async def test_reconcile_skips_past_jobs(self):
        """Jobs scheduled in the past are not re-registered."""
        with patch("app.agents.scheduler_agent.get_supabase_service_client") as mock_get_client:
            mock_supabase = MagicMock()
            mock_get_client.return_value = mock_supabase

            # One future, one past
            past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

            mock_execute = MagicMock()
            mock_execute.data = [
                {"post_id": "post-past", "scheduled_at": past_date},
                {"post_id": "post-future", "scheduled_at": future_date},
            ]
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_execute

            with patch("app.agents.scheduler_agent._scheduler") as mock_sched:
                mock_sched.add_job = MagicMock()

                await reconcile_scheduled_jobs()

                # Only future job added
                mock_sched.add_job.assert_called_once()
                call_args = mock_sched.add_job.call_args
                assert call_args.kwargs["id"] == "post_post-future"


class TestSchedulerConstants:
    """Constants used by scheduler."""

    def test_max_retries_is_3(self):
        assert MAX_RETRIES == 3

    def test_retry_base_delay_60_seconds(self):
        assert RETRY_BASE_DELAY == 60

    def test_retry_max_delay_3600_seconds(self):
        assert RETRY_MAX_DELAY == 3600


class TestPublishResult:
    """PublishResult dataclass."""

    def test_publish_result_success(self):
        result = PublishResult(
            success=True,
            status="published",
            platform_post_id="ig-123",
            platform_permalink="https://instagram.com/p/ig-123/",
        )
        assert result.success is True
        assert result.platform_post_id == "ig-123"

    def test_publish_result_failed(self):
        result = PublishResult(
            success=False,
            status="failed",
            failure_reason="Rate limited",
        )
        assert result.success is False
        assert result.failure_reason == "Rate limited"