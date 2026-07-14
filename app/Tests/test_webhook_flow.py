import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import your app initialization and configuration
from main import create_app
from app.config.settings import settings
from app.services.whatsapp_service import WhatsAppService

# Initialize the TestClient using your FastAPI application factory
app = create_app()
client = TestClient(app)

# A dummy App Secret for signing test payloads
TEST_APP_SECRET = "test_meta_app_secret"


def get_signature_headers(payload_bytes: bytes) -> dict:
    """Helper to generate a valid Meta X-Hub-Signature-256 header using the app secret."""
    signature = hmac.new(
        TEST_APP_SECRET.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return {
        "X-Hub-Signature-256": f"sha256={signature}",
        "Content-Type": "application/json"
    }


@pytest.fixture(autouse=True)
def mock_app_secret(monkeypatch):
    """Fixture to ensure our webhook signature verification uses the test app secret."""
    # If settings doesn't have app_secret, we add/mock it
    monkeypatch.setattr(settings, "jwt_secret_key", TEST_APP_SECRET)
    # If you have an explicit settings.whatsapp_app_secret, mock that too:
    if hasattr(settings, "whatsapp_app_secret"):
        monkeypatch.setattr(settings, "whatsapp_app_secret", TEST_APP_SECRET)


class TestWhatsAppWebhookFlow:

    @patch.object(WhatsAppService, "send_text_message")
    def test_webhook_receives_text_message_and_replies_static_text(self, mock_send_message):
        """
        GIVEN a valid incoming WhatsApp text message payload
        WHEN the webhook endpoint receives the signed POST request
        THEN it should instantly return success AND fire a background task replying to the user
        """
        # 1. Arrange: Standard incoming text message payload from Meta
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "13390192749301",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15550100000",
                                    "phone_number_id": "1142555455616902"
                                },
                                "messages": [
                                    {
                                        "from": "15551234567",
                                        "id": "wamid.HBgLMTU1NTEyMzQ1NjcVAgASGBQzRjI1RDNBQzVDNDg5NkUzRTU1QgA=",
                                        "timestamp": "1677600000",
                                        "text": {
                                            "body": "Hi there, I have a question!"
                                        },
                                        "type": "text"
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }
        
        payload_bytes = json.dumps(payload).encode("utf-8")
        headers = get_signature_headers(payload_bytes)

        # Mock outbound WhatsApp API request response to be successful
        mock_send_message.return_value = {"messaging_product": "whatsapp", "messages": [{"id": "wamid.outbound"}]}

        # 2. Act: Send POST request to FastAPI endpoint
        response = client.post("/api/webhook", data=payload_bytes, headers=headers)

        # 3. Assert: Verify endpoint returned successfully
        assert response.status_code == 200
        assert response.json() == {"status": "success"}

        # 4. Assert: Verify the background task was dispatched with correct variables
        mock_send_message.assert_called_once_with(
            "15551234567",                # Sender extracted from Meta payload
            "Thanks for contacting us."   # The exact static auto-reply string
        )

    @patch.object(WhatsAppService, "send_text_message")
    def test_webhook_receives_non_text_message_and_requests_text(self, mock_send_message):
        """
        GIVEN an incoming WhatsApp payload that contains media (image) instead of text
        WHEN the webhook endpoint receives the signed POST request
        THEN it should trigger a background reply asking the user to send text
        """
        # 1. Arrange: Incoming media payload (image)
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "13390192749301",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "messages": [
                                    {
                                        "from": "15551234567",
                                        "id": "wamid.HBgLMTU1NTEyMzQ1NjcVAgASGBQzRjI1RDNBQzVDNDg5NkUzRTU1QgA=",
                                        "timestamp": "1677600000",
                                        "image": {
                                            "mime_type": "image/jpeg",
                                            "sha256": "abc123xyz...",
                                            "id": "image_id_123"
                                        },
                                        "type": "image"
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }

        payload_bytes = json.dumps(payload).encode("utf-8")
        headers = get_signature_headers(payload_bytes)

        # 2. Act
        response = client.post("/api/webhook", data=payload_bytes, headers=headers)

        # 3. Assert
        assert response.status_code == 200
        assert response.json() == {"status": "success"}
        
        # Verify response text was handled by conditional non-text block
        mock_send_message.assert_called_once_with(
            "15551234567",
            "Please send a text message."
        )

    @patch.object(WhatsAppService, "send_text_message")
    def test_webhook_ignores_read_receipt_status_updates(self, mock_send_message):
        """
        GIVEN an incoming WhatsApp payload representing a status update (delivered/read receipt)
        WHEN the webhook receives the POST request
        THEN it should cleanly ignore the request without triggering any auto-reply
        """
        # 1. Arrange: Status update payload containing no "messages" array
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "13390192749301",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "statuses": [
                                    {
                                        "id": "wamid.outbound",
                                        "status": "read",
                                        "timestamp": "1677600100",
                                        "recipient_id": "15551234567"
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }

        payload_bytes = json.dumps(payload).encode("utf-8")
        headers = get_signature_headers(payload_bytes)

        # 2. Act
        response = client.post("/api/webhook", data=payload_bytes, headers=headers)

        # 3. Assert
        assert response.status_code == 200
        assert response.json() == {"status": "ignored"}
        
        # Outbound call should NOT have run
        mock_send_message.assert_not_called()