"""Shared pytest fixtures for social-media-manager backend tests.

All external dependencies (Supabase, Ollama, Instagram Graph API) are mocked here.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set DEBUG before importing app so mock fallback activates
os.environ["DEBUG"] = "true"

from app.core.config import settings
from app.core.database import get_supabase_client, get_supabase_service_client
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _debug_env():
    """Ensure DEBUG=true for all tests to enable mock fallbacks."""
    settings.DEBUG = True
    yield


def _make_mock_supabase():
    """Create a properly mocked Supabase client."""
    mock = MagicMock()

    # --- auth.get_user() ---
    mock_user = MagicMock()
    mock_user.id = "test-user-id"
    mock_user.email = "test@example.com"
    mock_auth_result = MagicMock()
    mock_auth_result.user = mock_user
    mock.auth.get_user.return_value = mock_auth_result

    # --- table().select().execute() chain ---
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_execute = MagicMock()

    mock_table.select.return_value = mock_select
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.in_.return_value = mock_table
    mock_table.gte.return_value = mock_table
    mock_table.lte.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.single.return_value = mock_execute
    mock_table.maybe_single.return_value = mock_execute
    mock_table.execute.return_value = mock_execute

    # Default empty data
    mock_execute.data = []

    mock.table.return_value = mock_table

    return mock, mock_table, mock_execute, mock_select, mock_auth_result


@pytest.fixture
def mock_supabase():
    """Mock Supabase client with common table/auth responses."""
    client, table, execute, select, auth_result = _make_mock_supabase()
    
    # Service client (separate instance for scheduler)
    service_client, service_table, service_execute, service_select, _ = _make_mock_supabase()
    service_client.auth.get_user.return_value = auth_result

    return {
        "client": client, 
        "service": service_client, 
        "table": table, 
        "execute": execute, 
        "select": select,
        "service_table": service_table,
        "service_execute": service_execute,
    }


@pytest.fixture
def mock_ollama():
    """Mock Ollama HTTP client for agent tests."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Default successful response for generate endpoint
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Mocked AI response",
            "done": True,
        }
        mock_client.post.return_value = mock_response

        yield mock_client


@pytest.fixture
def client(mock_supabase):
    """FastAPI TestClient with Supabase dependency overridden."""
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase["client"]
    app.dependency_overrides[get_supabase_service_client] = lambda: mock_supabase["service"]

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_scheduler():
    """Mock APScheduler for scheduler agent tests."""
    with patch("app.agents.scheduler_agent.get_scheduler") as mock_get:
        mock_sched = MagicMock()
        mock_sched.running = True
        mock_sched.get_job.return_value = None
        mock_get.return_value = mock_sched
        yield mock_sched