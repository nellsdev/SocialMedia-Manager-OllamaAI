"""Test WhatsApp webhook parsing and idea creation (Task 6.5)."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_supabase_client, get_supabase_service_client


class TestWhatsAppWebhook:
    """POST /api/ideas/whatsapp or /api/whatsapp webhook."""

    @pytest.fixture
    def whatsapp_client(self, mock_supabase):
        """TestClient with WhatsApp-specific mocks."""
        from app.core.database import get_supabase_client, get_supabase_service_client

        app.dependency_overrides[get_supabase_client] = lambda: mock_supabase["client"]
        app.dependency_overrides[get_supabase_service_client] = lambda: mock_supabase["service"]

        client = TestClient(app)
        yield client

        app.dependency_overrides.clear()

    def test_whatsapp_webhook_valid_message_creates_idea(self, whatsapp_client, mock_supabase):
        """Valid WhatsApp message -> creates idea in DB."""
        mock_execute = mock_supabase["execute"]
        mock_insert_resp = MagicMock()
        mock_insert_resp.data = [{"id": "idea-new-123"}]
        mock_execute.reset_mock()
        mock_supabase["table"].return_value.insert.return_value.execute.return_value = mock_insert_resp

        payload = {
            "message": "Amazing productivity tip: batch your tasks!",
            "media_urls": ["https://example.com/screenshot.png"],
        }

        response = whatsapp_client.post("/api/ideas/whatsapp", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "idea-new-123"

        # Verify insert was called with idea data
        mock_supabase["table"].assert_called_with("content_ideas")

    def test_whatsapp_webhook_empty_message_returns_400(self, whatsapp_client):
        """Empty message returns validation error."""
        payload = {"message": "", "media_urls": []}
        response = whatsapp_client.post("/api/ideas/whatsapp", json=payload)
        assert response.status_code == 422  # Pydantic validation

    def test_whatsapp_webhook_missing_message_field(self, whatsapp_client):
        """Missing message field returns 422."""
        payload = {"media_urls": ["https://example.com/img.jpg"]}
        response = whatsapp_client.post("/api/ideas/whatsapp", json=payload)
        assert response.status_code == 422

    def test_whatsapp_webhook_optional_media_urls(self, whatsapp_client, mock_supabase):
        """media_urls is optional, can be omitted or empty."""
        mock_execute = mock_supabase["execute"]
        mock_insert_resp = MagicMock()
        mock_insert_resp.data = [{"id": "idea-no-media"}]
        mock_execute.reset_mock()
        mock_supabase["table"].return_value.insert.return_value.execute.return_value = mock_insert_resp

        payload = {"message": "Text only idea"}
        response = whatsapp_client.post("/api/ideas/whatsapp", json=payload)

        assert response.status_code == 200
        assert response.json()["id"] == "idea-no-media"

    def test_whatsapp_webhook_db_error_returns_500(self, whatsapp_client, mock_supabase):
        """Database error during insert -> 500."""
        mock_supabase["table"].return_value.insert.return_value.execute.side_effect = Exception("DB down")

        payload = {"message": "Test idea"}
        response = whatsapp_client.post("/api/ideas/whatsapp", json=payload)

        assert response.status_code == 500


class TestWhatsAppConfig:
    """GET /api/whatsapp/status, POST /api/whatsapp/connect."""

    @pytest.fixture
    def wa_client(self, mock_supabase):
        from app.core.database import get_supabase_client, get_supabase_service_client
        app.dependency_overrides[get_supabase_client] = lambda: mock_supabase["client"]
        app.dependency_overrides[get_supabase_service_client] = lambda: mock_supabase["service"]
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_whatsapp_status_no_account(self, wa_client, mock_supabase):
        """No WhatsApp account connected -> connected=false."""
        mock_supabase["execute"].data = []  # no social_accounts with platform=whatsapp

        response = wa_client.get("/api/whatsapp/status")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert data["phone"] is None

    def test_whatsapp_connect_returns_qr(self, wa_client, mock_supabase):
        """POST /api/whatsapp/connect returns QR code for pairing."""
        # Mock the WhatsApp Cloud API response
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"code": "qr-code-data-123"}
            mock_client.post.return_value = mock_resp

            response = wa_client.post("/api/whatsapp/connect", json={"from_number": "+15551234567"})

            assert response.status_code == 200
            data = response.json()
            assert "qr_code" in data