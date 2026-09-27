"""Test agent prompt builders and Ollama interactions (Task 6.3)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.base import BaseAgent, ProfileStrategy
from app.agents.content_creator import ContentCreatorAgent
from app.agents.trend_researcher import TrendResearcherAgent
from app.agents.analytics_agent import AnalyticsAgent
from app.agents.scheduler_agent import SchedulerAgent, PublishResult
from app.agents.idea_bank import IdeaBankAgent


class TestProfileStrategy:
    """ProfileStrategy dataclass used by all agents."""

    def test_profile_strategy_creation(self):
        """All fields accepted."""
        strategy = ProfileStrategy(
            profile_id="profile-123",
            archetype="authority_professional",
            voice_description="Expert but accessible",
            content_pillars=["tech", "career", "leadership"],
            target_audience="Senior developers",
            goals="Build authority",
            visual_references=["https://example.com/ref.jpg"],
        )
        assert strategy.archetype == "authority_professional"
        assert len(strategy.content_pillars) == 3
        assert strategy.profile_id == "profile-123"

    def test_profile_strategy_minimal(self):
        """Only required fields."""
        strategy = ProfileStrategy(
            profile_id="profile-456",
            archetype="personal_sharing",
            voice_description="Casual",
            content_pillars=["life"],
            target_audience="Friends",
            goals="Share moments",
            visual_references=[],
        )
        assert strategy.archetype == "personal_sharing"
        assert strategy.profile_id == "profile-456"


class TestContentCreatorAgent:
    """ContentCreatorAgent prompt building + Ollama call."""

    @pytest.mark.asyncio
    async def test_generate_captions_builds_prompt(self, mock_ollama):
        """suggest_captions calls Ollama with archetype-aware prompt."""
        agent = ContentCreatorAgent()

        strategy = ProfileStrategy(
            profile_id="profile-123",
            archetype="aspiring_influencer",
            voice_description="Energetic, emoji-heavy",
            content_pillars=["lifestyle", "fashion"],
            target_audience="Gen Z",
            goals="Grow following",
            visual_references=[],
        )
        agent.profile = strategy

        # Mock the internal ollama client call
        with patch.object(agent, "_ollama_generate", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '[{"text": "Caption 1 💫", "tone": "energetic", "length": "short", "pillar": "lifestyle"}, {"text": "Caption 2 ✨", "tone": "fun", "length": "medium", "pillar": "fashion"}, {"text": "Caption 3 🌟", "tone": "inspiring", "length": "short", "pillar": "lifestyle"}]'

            result = await agent.suggest_captions(
                post_context="New outfit!",
                n=3,
            )

        # Verify Ollama was called
        mock_call.assert_called_once()
        call_args = mock_call.call_args[0][0]  # first positional arg = prompt
        assert "aspiring_influencer" in call_args
        assert "Energetic" in call_args
        assert "lifestyle" in call_args
        assert "New outfit!" in call_args

        # Verify result parsed
        assert isinstance(result, list)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_generate_hashtags(self, mock_ollama):
        """suggest_hashtags returns list of tags."""
        agent = ContentCreatorAgent()
        strategy = ProfileStrategy(
            profile_id="profile-123",
            archetype="business_owner",
            voice_description="Professional",
            content_pillars=["saas", "productivity"],
            target_audience="Founders",
            goals="Leads",
            visual_references=[],
        )
        agent.profile = strategy

        with patch.object(agent, "_ollama_generate", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '["#saas", "#productivity", "#founderlife", "#b2b", "#startup"]'

            result = await agent.suggest_hashtags(
                caption="Launching our new feature!",
                pillars=["saas", "productivity"],
            )

        assert isinstance(result, list)
        assert all(isinstance(tag, str) for tag in result)
        assert "saas" in result  # parser strips #

    @pytest.mark.asyncio
    async def test_recommend_format(self, mock_ollama):
        """suggest_format returns one of 4 valid formats."""
        agent = ContentCreatorAgent()
        strategy = ProfileStrategy(
            profile_id="profile-123",
            archetype="community_builder",
            voice_description="Warm",
            content_pillars=["community"],
            target_audience="Members",
            goals="Engagement",
            visual_references=[],
        )
        agent.profile = strategy

        with patch.object(agent, "_ollama_generate", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '{"format": "reel", "reasoning": "Best for engagement"}'

            result = await agent.suggest_format(
                idea="Behind the scenes",
            )

        assert result.format in ["story", "carousel", "reel", "live"]
        assert isinstance(result.reasoning, str)


class TestTrendResearcherAgent:
    """TrendResearcherAgent fetches trends."""

    @pytest.mark.asyncio
    async def test_research_trends_returns_topics(self, mock_ollama):
        """get_trending_topics returns list of trend objects."""
        agent = TrendResearcherAgent()
        strategy = ProfileStrategy(
            profile_id="profile-123",
            archetype="authority_professional",
            voice_description="Expert",
            content_pillars=["ai", "ml"],
            target_audience="Engineers",
            goals="Thought leadership",
            visual_references=[],
        )
        agent.profile = strategy

        with patch.object(agent, "_ollama_generate", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '[{"topic": "LLM fine-tuning", "description": "How to fine-tune", "relevance": "high"}, {"topic": "RAG patterns", "description": "RAG for enterprise", "relevance": "medium"}]'

            result = await agent.get_trending_topics(niche="AI")

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].topic == "LLM fine-tuning"
        assert result[0].relevance == "high"


class TestAnalyticsAgent:
    """AnalyticsAgent engagement calculations."""

    def test_calculate_engagement_rate(self):
        """compute_engagement_rate matches formula."""
        agent = AnalyticsAgent()

        # Standard case
        import asyncio
        rate = asyncio.run(agent.compute_engagement_rate(likes=100, comments=20, reach=1000))
        assert rate == 12.0

        # Zero reach
        rate = asyncio.run(agent.compute_engagement_rate(likes=10, comments=5, reach=0))
        assert rate == 0.0

        # Large numbers
        rate = asyncio.run(agent.compute_engagement_rate(likes=10000, comments=500, reach=50000))
        assert rate == 21.0

    def test_calculate_engagement_rate_precision(self):
        """Rate rounded to 2 decimals."""
        agent = AnalyticsAgent()
        import asyncio
        rate = asyncio.run(agent.compute_engagement_rate(likes=7, comments=3, reach=1000))
        assert rate == 1.0  # (7+3)/1000*100 = 1.0


class TestSchedulerAgent:
    """SchedulerAgent APScheduler integration."""

    @pytest.mark.asyncio
    async def test_schedule_post_registers_job(self, mock_scheduler):
        """schedule_post adds job to scheduler."""
        agent = SchedulerAgent()

        from datetime import datetime, timezone, timedelta
        scheduled_for = datetime.now(timezone.utc) + timedelta(hours=1)

        # Mock the job returned by add_job
        mock_job = MagicMock()
        mock_job.id = "post_post-123"
        mock_scheduler.add_job.return_value = mock_job

        job_id = await agent.schedule_post(post_id="post-123", scheduled_for=scheduled_for)

        mock_scheduler.add_job.assert_called_once()
        call_kwargs = mock_scheduler.add_job.call_args.kwargs
        assert call_kwargs["id"] == "post_post-123"
        assert call_kwargs["trigger"] == "date"
        assert job_id == "post_post-123"

    @pytest.mark.asyncio
    async def test_cancel_post_removes_job(self, mock_scheduler):
        """cancel_post removes job from scheduler."""
        agent = SchedulerAgent()
        mock_scheduler.get_job.return_value = MagicMock()  # job exists

        result = await agent.cancel_post(post_id="post-123")

        assert result is True
        mock_scheduler.remove_job.assert_called_once_with("post_post-123")

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_post(self, mock_scheduler):
        """cancel_post returns False if job not found."""
        agent = SchedulerAgent()
        mock_scheduler.get_job.return_value = None
        mock_scheduler.remove_job.side_effect = Exception("Job not found")

        result = await agent.cancel_post(post_id="post-999")
        assert result is False

    @pytest.mark.asyncio
    async def test_publish_post_no_account_returns_failed(self, mock_scheduler):
        """publish_post with no linked IG account returns failed result."""
        agent = SchedulerAgent()

        # Mock supabase to return post without ig_account_id
        with patch("app.agents.scheduler_agent.get_supabase_service_client") as mock_get_client:
            mock_supabase = MagicMock()
            mock_get_client.return_value = mock_supabase

            # Post exists but no ig_account_id
            mock_post_resp = MagicMock()
            mock_post_resp.data = {"id": "post-123", "ig_account_id": None}
            mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_post_resp

            result = await agent.publish_post(post_id="post-123")

        assert isinstance(result, PublishResult)
        assert result.success is False
        assert result.status == "failed"
        assert "No Instagram account" in result.failure_reason


class TestIdeaBankAgent:
    """IdeaBankAgent WhatsApp processing."""

    @pytest.mark.asyncio
    async def test_process_whatsapp_message_creates_idea(self, mock_ollama):
        """process_whatsapp_message persists idea before enrichment."""
        agent = IdeaBankAgent()
        strategy = ProfileStrategy(
            profile_id="profile-123",
            archetype="personal_sharing",
            voice_description="Casual",
            content_pillars=["life", "tips"],
            target_audience="Friends",
            goals="Share",
            visual_references=[],
        )
        agent.profile = strategy

        with patch("app.agents.idea_bank.get_supabase_service_client") as mock_get_client:
            mock_supabase = MagicMock()
            mock_get_client.return_value = mock_supabase

            # Mock insert response
            mock_insert_resp = MagicMock()
            mock_insert_resp.data = [{"id": "idea-123"}]
            mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_resp

            # Mock update responses for enrichment
            mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

            # Mock Ollama for auto-tagging
            with patch.object(agent, "_ollama_generate", new_callable=AsyncMock) as mock_call:
                mock_call.side_effect = [
                    '{"pillar": "tips"}',  # auto_tag_pillar
                    '{"format": "reel", "reasoning": "Visual content"}',  # suggest_format_from_text
                ]

                result = await agent.process_whatsapp_message(
                    text="Great productivity tip!",
                    media=["https://example.com/img.jpg"],
                    from_number="+15551234567",
                )

        assert result["id"] == "idea-123"
        mock_supabase.table.assert_called()  # insert called