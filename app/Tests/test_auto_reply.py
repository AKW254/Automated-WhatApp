import json
import hmac
import hashlib
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import create_app
from app.config.settings import settings

def get_signature(payload_bytes: bytes, secret: str) -> str:
    """Generate Meta X-Hub-Signature-256 header"""
    signature = hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={signature}"


class TestAutoReply:

    def setup_method(self):
        """Create a fresh application and test client."""
        self.app = create_app()
        self.client = TestClient(self.app)

        # Payload based on the real payload received from Meta.
        self.webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                 "id": "1339019927749301",
                 "changes": [
                     {
                            "value": {
                             "messaging_product": "whatsapp",
                             "metadata": {
                                "display_phone_number": "15556236073",
                                "phone_number_id": "1142555455616902",
                                },
                                "contacts": [
                                {
                                    "profile": {
                                        "name": "Antony wambua",
                                    },
                                    "wa_id": "254799155770",
                                    "user_id": "KE.3287753374740578",
                                    "country_code": "KE",
                                }
                            ],
                            "messages": [
                                {
                                    "from": "254799155770",
                                    "from_user_id": "KE.3287753374740578",
                                    "id": "wamid.test123",
                                    "timestamp": "1786098178",
                                    "text": {
                                        "body": "Hello",
                                    },
                                    "from_logical_id": "26289679397100",
                                    "type": "text",
                                    "internal_1p_only_data": {
                                        "account_context": {
                                            "waac_id": "2320609795412191",
                                            "cs_id": "1142555455616902",
                                            "account_context_type": "non_paid_messaging",
                                        }
                                    },
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }

# ------------------------------------------------------------------
# Test 1
# ------------------------------------------------------------------

    def test_webhook_verification(self):
        """Verify that Meta webhook verification works."""
        response = self.client.get(
            "/api/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "test_challenge_123",
                "hub.verify_token": settings.whatsapp_verify_token,
            },
        )

        print(f"Verification status: {response.status_code}")
        print(f"Verification response: {response.text}")

        assert response.status_code == 200
        assert response.text == "test_challenge_123"

# ------------------------------------------------------------------
# Test 2
# ------------------------------------------------------------------

    def test_webhook_receives_text_message(self):
        """
        Verify that a valid Meta webhook reaches the WhatsApp handler.
        """
        payload_bytes = json.dumps(
            self.webhook_payload
        ).encode("utf-8")

        signature = get_signature(
            payload_bytes,
            settings.whatsapp_app_secret or "test_secret",
        )

        headers = {
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        }

        message = (
            self.webhook_payload["entry"][0]
            ["changes"][0]["value"]["messages"][0]
        )

        print("\n" + "=" * 60)
        print("TEST: Webhook Text Message")
        print("=" * 60)
        print(f"Message: {message['text']['body']}")
        print(f"From: {message['from']}")

        with patch(
            "app.services.whatsapp_service.WhatsAppService.process_message"
        ) as mock_process:

            response = self.client.post(
                "/api/webhook",
                content=payload_bytes,
                headers=headers,
            )

        print(f"Webhook status: {response.status_code}")
        print(f"Webhook response: {response.text}")

        assert response.status_code == 200
        assert response.text == "OK"

        assert mock_process.called, (
            "WhatsAppService.process_message was not called"
        )

        mock_process.assert_called_once()

        processed_message = mock_process.call_args.args[0]

        assert processed_message.from_ == "254799155770"
        assert processed_message.type == "text"
        assert processed_message.text == "Hello"

# ------------------------------------------------------------------
# Test 3
# ------------------------------------------------------------------

    def test_text_message_generates_auto_reply(self):
        """Verify that a text message generates the expected reply."""

        from pywa.types import Message as PywaMessage
        from app.services.whatsapp_service import WhatsAppService

        mock_msg = MagicMock(spec=PywaMessage)

        mock_msg.from_ = "254799155770"
        mock_msg.type = "text"
        mock_msg.text = "Hello"
        mock_msg.id = "wamid.test123"
        mock_msg.timestamp = "1786098178"

        WhatsAppService.process_message(mock_msg)

        mock_msg.reply_text.assert_called_once()

        response = mock_msg.reply_text.call_args.args[0]

        print("\nAuto-reply:")
        print(response)

        assert "Hello" in response
        assert "assistant" in response.lower()
        assert "shortly" in response.lower()

# ------------------------------------------------------------------
# Test 4
# ------------------------------------------------------------------

    def test_non_text_message_generates_text_request(self):
        """Verify that non-text messages receive the correct response."""

        from pywa.types import Message as PywaMessage
        from app.services.whatsapp_service import WhatsAppService

        mock_msg = MagicMock(spec=PywaMessage)

        mock_msg.from_ = "254799155770"
        mock_msg.type = "image"
        mock_msg.text = None
        mock_msg.id = "wamid.test456"

        WhatsAppService.process_message(mock_msg)

        mock_msg.reply_text.assert_called_once()

        response = mock_msg.reply_text.call_args.args[0]

        print("\nNon-text reply:")
        print(response)

        assert "text message" in response.lower()

# ------------------------------------------------------------------
# Test 5
# ------------------------------------------------------------------

    def test_message_processing_handles_reply_error(self):
        """Verify that reply errors are handled without crashing."""

        from pywa.types import Message as PywaMessage
        from app.services.whatsapp_service import WhatsAppService

        mock_msg = MagicMock(spec=PywaMessage)

        mock_msg.from_ = "254799155770"
        mock_msg.type = "text"
        mock_msg.text = "Hello"
        mock_msg.id = "wamid.test789"

        mock_msg.reply_text.side_effect = Exception(
            "API Error: Invalid token"
        )

        # process_message catches the error internally.
        WhatsAppService.process_message(mock_msg)

        mock_msg.reply_text.assert_called()

# ------------------------------------------------------------------
# Test 6
# ------------------------------------------------------------------

def test_real_payload_contains_required_pywa_fields(self):
    """
    Verify that the test fixture contains the fields PyWa requires
    when constructing a Message object.
    """

    value = self.webhook_payload["entry"][0]["changes"][0]["value"]

    contact = value["contacts"][0]
    message = value["messages"][0]

    assert contact["wa_id"]
    assert contact["user_id"]
    assert contact["country_code"]

    assert message["from"]
    assert message["id"]
    assert message["timestamp"]
    assert message["type"] == "text"
    assert message["text"]["body"]

# ------------------------------------------------------------------
# Test 7
# ------------------------------------------------------------------

def test_webhook_rejects_invalid_signature(self):
    """Verify that an invalid Meta signature is rejected."""

    payload_bytes = json.dumps(
        self.webhook_payload
    ).encode("utf-8")

    headers = {
        "X-Hub-Signature-256": "sha256=invalid_signature",
        "Content-Type": "application/json",
    }

    response = self.client.post(
        "/api/webhook",
        content=payload_bytes,
        headers=headers,
    )

    print(
        f"\nInvalid signature status: "
        f"{response.status_code}"
        )

    assert response.status_code in (400, 401, 403)


if __name__ == "__main__":
    import pytest

    raise SystemExit(
        pytest.main(
            [
                __file__,
                "-v",
                "-s",
            ]
        )
    )

