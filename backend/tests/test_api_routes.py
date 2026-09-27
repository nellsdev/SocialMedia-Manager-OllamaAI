"""Test API routes with FastAPI TestClient (Task 6.2 - additional routes)."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.core.database import get_supabase_client, get_supabase_service_client


class TestAuthRoutes:
    """POST /api/auth/register, POST /api/auth/login, GET /api/auth/session"""

    @pytest.fixture
    def auth_client(self, mock_supabase):
        app.dependency_overrides[get_supabase_client] = lambda: mock_supabase["client"]
        app.dependency_overrides[get_supabase_service_client] = lambda: mock_supabase["service"]
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_register_returns_user_id(self, auth_client, mock_supabase):
        """Register returns user_id on success."""
        mock_execute = mock_supabase["execute"]
        mock_execute.data = [{"id": "new-user-id"}]

        response = auth_client.post("/api/auth/register", json={
            "email": "newuser@example.com",
            "password": "securepass123"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "new-user-id"

    def test_login_returns_session_token(self, auth_client, mock_supabase):
        """Login returns session_token + user_id."""
        mock_execute = mock_supabase["execute"]
        mock_execute.data = [{"id": "existing-user", "email": "user@example.com"}]

        response = auth_client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "securepass123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "session_token" in data
        assert data["user_id"] == "existing-user"

    def test_session_returns_user_profile(self, auth_client, mock_supabase):
        """GET /api/auth/session returns user + profile."""
        mock_execute = mock_supabase["execute"]
        mock_execute.data = {"id": "user-123", "email": "user@example.com"}

        # Mock profile lookup
        mock_supabase["table"].return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
            "id": "profile-123",
            "user_id": "user-123",
            "name": "Personal",
            "archetype": "personal_sharing",
        }

        response = auth_client.get("/api/auth/session")
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["id"] == "user-123"
        assert data["profile"]["archetype"] == "personal_sharing"


class TestIdeasRoutes:
    """GET /api/ideas, POST /api/ideas, PUT /api/ideas/{id}/convert"""

    @pytest.fixture
    def ideas_client(self, mock_supabase):
        app.dependency_overrides[get_supabase_client] = lambda: mock_supabase["client"]
        app.dependency_overrides[get_supabase_service_client] = lambda: mock_supabase["service"]
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_get_ideas_returns_list(self, ideas_client, mock_supabase):
        """GET /api/ideas returns list of ideas."""
        mock_execute = mock_supabase["execute"]
        mock_execute.data = [
            {"id": "idea-1", "title": "Idea 1", "status": "idea"},
            {"id": "idea-2", "title": "Idea 2", "status": "converted"},
        ]

        response = ideas_client.get("/api/ideas")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Idea 1"

    def test_get_ideas_with_filters(self, ideas_client, mock_supabase):
        """Query params pillar, status, source passed to query."""
        mock_execute = mock_supabase["execute"]
        mock_execute.data = []

        response = ideas_client.get("/api/ideas?pillar=education&status=idea&source=manual")
        assert response.status_code == 200

        # Verify filters applied
        select_mock = mock_supabase["select"]
        select_mock.eq.assert_any_call("pillar", "education")
        select_mock.eq.assert_any_call("status", "idea")

    def test_post_idea_creates_new(self, ideas_client, mock_supabase):
        """POST /api/ideas creates new idea."""
        mock_execute = mock_supabase["execute"]
        mock_insert = MagicMock()
        mock_insert.data = [{"id": "idea-new-456"}]
        mock_execute.reset_mock()
        mock_supabase["table"].return_value.insert.return_value.execute.return_value = mock_insert

        response = ideas_client.post("/api/ideas", json={
            "title": "New idea",
            "description": "Details here",
            "suggested_format": "reel",
            "content_pillar": "education",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "idea-new-456"

    def test_convert_idea_creates_post(self, ideas_client, mock_supabase):
        """PUT /api/ideas/{id}/convert creates post from idea."""
        # Mock idea exists
        mock_idea_execute = MagicMock()
        mock_idea_execute.data = {
            "id": "idea-123",
            "title": "Convert me",
            "description": "Desc",
            "suggested_format": "carousel",
            "content_pillar": "tips",
        }

        # Mock post insert
        mock_post_execute = MagicMock()
        mock_post_execute.data = [{"id": "post-789"}]

        mock_supabase["table"].side_effect = lambda name: {
            "content_ideas": MagicMock(
                select=lambda *a, **kw: MagicMock(
                    eq=lambda *a, **kw: MagicMock(
                        maybe_single=lambda: MagicMock(execute=lambda: mock_idea_execute)
                    )
                ),
                update=lambda *a, **kw: MagicMock(
                    eq=lambda *a, **kw: MagicMock(execute=MagicMock())
                ),
            ),
            "content_posts": MagicMock(
                insert=lambda *a, **kw: MagicMock(execute=lambda: mock_post_execute)
            ),
        }.get(name, MagicMock())

        response = ideas_client.put("/api/ideas/idea-123/convert")
        assert response.status_code == 200
        data = response.json()
        assert data["post_id"] == "post-789"


class TestPostsRoutes:
    """GET /api/posts, POST /api/posts, PUT /api/posts/{id}"""

    @pytest.fixture
    def posts_client(self, mock_supabase):
        app.dependency_overrides[get_supabase_client] = lambda: mock_supabase["client"]
        app.dependency_overrides[get_supabase_service_client] = lambda: mock_supabase["service"]
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_get_posts_returns_list(self, posts_client, mock_supabase):
        """GET /api/posts returns list."""
        mock_execute = mock_supabase["execute"]
        mock_execute.data = [
            {"id": "post-1", "title": "Post 1", "status": "draft"},
            {"id": "post-2", "title": "Post 2", "status": "published"},
        ]

        response = posts_client.get("/api/posts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_post_post_creates_draft(self, posts_client, mock_supabase):
        """POST /api/posts creates draft post."""
        mock_insert_execute = MagicMock()
        mock_insert_execute.data = [{"id": "post-new-123"}]
        mock_supabase["table"].return_value.insert.return_value.execute.return_value = mock_insert_execute

        response = posts_client.post("/api/posts", json={
            "format": "carousel",
            "title": "My Carousel",
            "caption": "Slide 1, Slide 2",
            "media_urls": ["https://example.com/1.jpg", "https://example.com/2.jpg"],
            "hashtags": ["#tip", "#carousel"],
        })

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "post-new-123"

    def test_put_post_updates_existing(self, posts_client, mock_supabase):
        """PUT /api/posts/{id} updates post."""
        mock_update_execute = MagicMock()
        mock_supabase["table"].return_value.update.return_value.eq.return_value.execute.return_value = mock_update_execute

        response = posts_client.put("/api/posts/post-123", json={
            "caption": "Updated caption",
        })

        assert response.status_code == 200


class TestGridRoutes:
    """GET /api/grid, GET /api/grid/distribution"""

    @pytest.fixture
    def grid_client(self, mock_supabase):
        app.dependency_overrides[get_supabase_client] = lambda: mock_supabase["client"]
        app.dependency_overrides[get_supabase_service_client] = lambda: mock_supabase["service"]
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_get_grid_returns_days(self, grid_client, mock_supabase):
        """GET /api/grid returns calendar days with posts."""
        mock_execute = mock_supabase["execute"]
        mock_execute.data = {
            "days": [
                {"date": "2026-01-15", "posts": [{"id": "post-1", "title": "Post 1"}]},
                {"date": "2026-01-16", "posts": []},
            ]
        }

        response = grid_client.get("/api/grid?view=month&date=2026-01-15")
        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        assert len(data["days"]) == 2

    def test_get_grid_distribution(self, grid_client, mock_supabase):
        """GET /api/grid/distribution returns pillar/format breakdown."""
        mock_execute = mock_supabase["execute"]
        mock_execute.data = {
            "pillars": [{"name": "education", "count": 5, "percentage": 50}],
            "formats": [{"name": "carousel", "count": 3, "percentage": 30}],
        }

        response = grid_client.get("/api/grid/distribution")
        assert response.status_code == 200
        data = response.json()
        assert "pillars" in data
        assert "formats" in data


class TestAgentsRoutes:
    """POST /api/agents/captions, /hashtags, /weekly-ideas"""

    @pytest.fixture
    def agents_client(self, mock_supabase, mock_ollama):
        app.dependency_overrides[get_supabase_client] = lambda: mock_supabase["client"]
        app.dependency_overrides[get_supabase_service_client] = lambda: mock_supabase["service"]
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_agents_captions_endpoint(self, agents_client):
        """POST /api/agents/captions returns 3 suggestions."""
        response = agents_client.post("/api/agents/captions", json={
            "post_content": "My new blog post!",
            "archetype": "authority_professional",
        })

        # In DEBUG mode with mocked Ollama, should return mock
        assert response.status_code == 200
        data = response.json()
        assert "options" in data
        assert len(data["options"]) == 3

    def test_agents_hashtags_endpoint(self, agents_client):
        """POST /api/agents/hashtags returns hashtag list."""
        response = agents_client.post("/api/agents/hashtags", json={
            "caption": "Launching our product!",
            "pillars": ["saas", "launch"],
        })

        assert response.status_code == 200
        data = response.json()
        assert "hashtags" in data
        assert isinstance(data["hashtags"], list)