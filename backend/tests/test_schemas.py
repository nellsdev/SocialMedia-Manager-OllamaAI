"""Test Pydantic schemas validation (Task 6.1)."""

import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest, LoginRequest
from app.schemas.ideas import IdeaCreate, IdeaConvertResponse
from app.schemas.posts import PostCreate
from app.schemas.profiles import StrategyUpdate
from app.schemas.dashboard import KpiResponse, TimeSeriesPoint, TimeSeriesResponse


class TestAuthSchemas:
    """Auth request validation."""

    def test_register_valid_email_password(self):
        """Valid email + password >= 8 chars passes."""
        data = RegisterRequest(email="user@example.com", password="securepass123")
        assert data.email == "user@example.com"
        assert data.password == "securepass123"

    def test_register_invalid_email_fails(self):
        """Invalid email format raises ValidationError."""
        with pytest.raises(ValidationError) as exc:
            RegisterRequest(email="not-an-email", password="securepass123")
        assert "email" in str(exc.value).lower()

    def test_register_short_password_accepted(self):
        """Current schema accepts short passwords (validation at Supabase Auth level)."""
        data = RegisterRequest(email="user@example.com", password="short")
        assert data.password == "short"

    def test_login_schema(self):
        """Login request validates email + password."""
        data = LoginRequest(email="user@example.com", password="securepass123")
        assert data.email == "user@example.com"


class TestIdeaSchemas:
    """Idea bank schemas."""

    def test_idea_create_minimal(self):
        """Minimal idea (title only) is valid."""
        idea = IdeaCreate(title="My content idea")
        assert idea.title == "My content idea"
        assert idea.description is None
        assert idea.suggested_format is None

    def test_idea_create_full(self):
        """Full idea with all optional fields."""
        idea = IdeaCreate(
            title="Reel idea",
            description="Dance tutorial",
            suggested_format="reel",
            content_pillar="education",
        )
        assert idea.suggested_format == "reel"
        assert idea.content_pillar == "education"

    def test_idea_convert_schema(self):
        """Convert idea -> post schema."""
        convert = IdeaConvertResponse(post_id="post-uuid-123")
        assert convert.post_id == "post-uuid-123"


class TestPostSchemas:
    """Post management schemas."""

    def test_post_create_all_formats(self):
        """All 4 Instagram formats accepted."""
        for fmt in ["story", "carousel", "reel", "live"]:
            post = PostCreate(
                format=fmt,
                title=f"{fmt} post",
                caption="Test caption",
                media_urls=["https://example.com/img.jpg"],
            )
            assert post.format == fmt

    def test_post_create_invalid_format_fails(self):
        """Invalid format raises ValidationError."""
        with pytest.raises(ValidationError):
            PostCreate(
                format="invalid_format",
                title="Test",
                caption="Caption",
                media_urls=[],
            )

    def test_post_format_validation(self):
        """PostCreate format field validates against allowed values."""
        # Valid formats
        for fmt in ["story", "carousel", "reel", "live"]:
            post = PostCreate(format=fmt, title="Test", caption="Caption", media_urls=[])
            assert post.format == fmt

        # Invalid format raises ValidationError
        with pytest.raises(ValidationError):
            PostCreate(format="invalid", title="Test", caption="Caption", media_urls=[])


class TestProfileSchemas:
    """Profile strategy schemas."""

    def test_strategy_update_partial(self):
        """Partial strategy update (only archetype) is valid."""
        update = StrategyUpdate(archetype="authority_professional")
        assert update.archetype == "authority_professional"
        assert update.voice_description is None
        assert update.content_pillars is None

    def test_strategy_update_full(self):
        """Full strategy update with all fields."""
        update = StrategyUpdate(
            archetype="business_owner",
            voice_description="Professional but friendly",
            content_pillars=["tips", "case_studies", "tools"],
            target_audience="Small business owners",
            goals="Generate leads",
        )
        assert len(update.content_pillars) == 3
        assert update.archetype == "business_owner"


class TestDashboardSchemas:
    """Dashboard response schemas."""

    def test_kpi_response_defaults(self):
        """KpiResponse defaults to zeros."""
        kpi = KpiResponse()
        assert kpi.followers == 0
        assert kpi.likes == 0
        assert kpi.comments == 0
        assert kpi.reach == 0
        assert kpi.engagement_rate == 0.0
        assert kpi.followers_delta == 0.0
        assert kpi.engagement_delta == 0.0

    def test_kpi_response_with_values(self):
        """KpiResponse accepts all fields."""
        kpi = KpiResponse(
            followers=1000,
            likes=500,
            comments=50,
            reach=5000,
            engagement_rate=11.0,
            followers_delta=5.5,
            engagement_delta=-1.2,
        )
        assert kpi.followers == 1000
        assert kpi.engagement_delta == -1.2

    def test_timeseries_point(self):
        """TimeSeriesPoint validates date + value."""
        point = TimeSeriesPoint(date="2026-01-15", value=123.5)
        assert point.date == "2026-01-15"
        assert point.value == 123.5

    def test_timeseries_response(self):
        """TimeSeriesResponse wraps metric + days + points."""
        resp = TimeSeriesResponse(
            metric="followers",
            days=7,
            data=[TimeSeriesPoint(date="2026-01-15", value=100), TimeSeriesPoint(date="2026-01-16", value=120)],
        )
        assert resp.metric == "followers"
        assert resp.days == 7
        assert len(resp.data) == 2