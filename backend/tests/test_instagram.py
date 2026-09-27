"""Test Instagram Graph API client with mocked responses (Task 6.6)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.agents.scheduler_agent import SchedulerAgent, PublishResult


class TestInstagramGraphAPI:
    """SchedulerAgent._publish_with_retry with mocked httpx responses."""

    @pytest.fixture
    def agent(self):
        return SchedulerAgent()

    @pytest.mark.asyncio
    async def test_publish_success_two_step_flow(self, agent):
        """Media creation + media_publish both succeed -> published."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Step 1: Create media container
            create_resp = MagicMock()
            create_resp.status_code = 200
            create_resp.json.return_value = {"id": "creation-123"}

            # Step 2: Publish media container
            publish_resp = MagicMock()
            publish_resp.status_code = 200
            publish_resp.json.return_value = {"id": "ig-post-456"}

            mock_client.post.side_effect = [create_resp, publish_resp]

            result = await agent._publish_with_retry(
                post_id="post-123",
                ig_user_id="17841400000000000",
                access_token="fake-token",
                media_type="CAROUSEL",
                media_url="https://example.com/img.jpg",
                caption="Test post",
            )

        assert isinstance(result, PublishResult)
        assert result.success is True
        assert result.status == "published"
        assert result.platform_post_id == "ig-post-456"
        assert result.platform_permalink == "https://www.instagram.com/p/ig-post-456/"

        # Verify both API calls made
        assert mock_client.post.call_count == 2
        create_call = mock_client.post.call_args_list[0]
        publish_call = mock_client.post.call_args_list[1]

        # Create media call
        assert "media" in create_call.args[0]
        assert create_call.kwargs["json"]["media_type"] == "CAROUSEL"
        assert create_call.kwargs["json"]["image_url"] == "https://example.com/img.jpg"

        # Publish call
        assert "media_publish" in publish_call.args[0]
        assert publish_call.kwargs["json"]["creation_id"] == "creation-123"

    @pytest.mark.asyncio
    async def test_publish_rate_limit_429_retries(self, agent):
        """429 on create media -> retries with exponential backoff."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # First call: 429 rate limited
            rate_limit_resp = MagicMock()
            rate_limit_resp.status_code = 429
            rate_limit_resp.json.return_value = {"error": {"message": "Rate limited"}}

            # Second call: success
            create_resp = MagicMock()
            create_resp.status_code = 200
            create_resp.json.return_value = {"id": "creation-789"}

            publish_resp = MagicMock()
            publish_resp.status_code = 200
            publish_resp.json.return_value = {"id": "ig-post-999"}

            mock_client.post.side_effect = [rate_limit_resp, create_resp, publish_resp]

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                result = await agent._publish_with_retry(
                    post_id="post-retry",
                    ig_user_id="17841400000000000",
                    access_token="fake-token",
                    media_type="IMAGE",
                    media_url="https://example.com/img.jpg",
                    caption="Retry test",
                )

            # Should have retried (3 calls: 429 + create + publish)
            assert mock_client.post.call_count == 3
            mock_sleep.assert_called()  # backoff sleep happened

            assert result.success is True
            assert result.status == "published"

    @pytest.mark.asyncio
    async def test_publish_max_retries_exhausted_returns_failed(self, agent):
        """All 3 attempts fail -> returns failed result."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # All 3 attempts return 500
            error_resp = MagicMock()
            error_resp.status_code = 500
            error_resp.json.return_value = {"error": {"message": "Internal server error"}}
            mock_client.post.return_value = error_resp

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await agent._publish_with_retry(
                    post_id="post-fail",
                    ig_user_id="17841400000000000",
                    access_token="fake-token",
                    media_type="REEL",
                    media_url="https://example.com/video.mp4",
                    caption="Will fail",
                )

            # 3 attempts * 2 calls each = 6 (create + publish each attempt)
            # Actually stops after create fails, so 3 create calls
            assert mock_client.post.call_count == 3

            assert result.success is False
            assert result.status == "failed"
            assert "All 3 attempts failed" in result.failure_reason

    @pytest.mark.asyncio
    async def test_publish_create_success_publish_fails_retries(self, agent):
        """Create succeeds, publish fails -> retries publish only."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Attempt 1: create OK, publish 500
            create_resp1 = MagicMock()
            create_resp1.status_code = 200
            create_resp1.json.return_value = {"id": "creation-A"}

            publish_resp1 = MagicMock()
            publish_resp1.status_code = 500
            publish_resp1.json.return_value = {"error": {"message": "Publish failed"}}

            # Attempt 2: create OK, publish OK
            create_resp2 = MagicMock()
            create_resp2.status_code = 200
            create_resp2.json.return_value = {"id": "creation-B"}

            publish_resp2 = MagicMock()
            publish_resp2.status_code = 200
            publish_resp2.json.return_value = {"id": "ig-post-success"}

            mock_client.post.side_effect = [
                create_resp1, publish_resp1,  # attempt 1
                create_resp2, publish_resp2,  # attempt 2
            ]

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await agent._publish_with_retry(
                    post_id="post-retry-publish",
                    ig_user_id="17841400000000000",
                    access_token="fake-token",
                    media_type="REEL",
                    media_url="https://example.com/video.mp4",
                    caption="Publish retry",
                )

            # 4 calls total (create+publish attempt 1, create+publish attempt 2)
            assert mock_client.post.call_count == 4
            assert result.success is True
            assert result.platform_post_id == "ig-post-success"

    @pytest.mark.asyncio
    async def test_publish_timeout_triggers_retry(self, agent):
        """httpx.TimeoutException triggers retry."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # First call: timeout
            mock_client.post.side_effect = [
                httpx.TimeoutException("Request timed out"),
                # Second attempt: success
                MagicMock(status_code=200, json=lambda: {"id": "creation-C"}),
                MagicMock(status_code=200, json=lambda: {"id": "ig-post-timeout-retry"}),
            ]

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await agent._publish_with_retry(
                    post_id="post-timeout",
                    ig_user_id="17841400000000000",
                    access_token="fake-token",
                    media_type="IMAGE",
                    media_url="https://example.com/img.jpg",
                    caption="Timeout test",
                )

            assert result.success is True

    @pytest.mark.asyncio
    async def test_publish_video_type_uses_video_url(self, agent):
        """REEL/VIDEO media_type sends video_url not image_url."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            create_resp = MagicMock()
            create_resp.status_code = 200
            create_resp.json.return_value = {"id": "creation-video"}

            publish_resp = MagicMock()
            publish_resp.status_code = 200
            publish_resp.json.return_value = {"id": "ig-video-123"}

            mock_client.post.side_effect = [create_resp, publish_resp]

            await agent._publish_with_retry(
                post_id="post-video",
                ig_user_id="17841400000000000",
                access_token="fake-token",
                media_type="REEL",
                media_url="https://example.com/reel.mp4",
                caption="Video post",
            )

            create_call = mock_client.post.call_args_list[0]
            payload = create_call.kwargs["json"]
            assert payload["media_type"] == "REEL"
            assert "video_url" in payload
            assert payload["video_url"] == "https://example.com/reel.mp4"
            assert "image_url" not in payload