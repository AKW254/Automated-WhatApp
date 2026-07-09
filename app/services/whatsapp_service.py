import requests

from app.config.settings import settings

class WhatsAppService:
    GRAPH_API_VERSION = "v25.0"

    @staticmethod
    def _graph_url() -> str:
        return (
            f"https://graph.facebook.com/"
            f"{WhatsAppService.GRAPH_API_VERSION}/"
            f"{settings.whatsapp_phone_number_id}/messages"
        )

    @staticmethod
    def send_text_message(
        recipient: str,
        message: str,
    ):
        headers = {
            "Authorization": (
                f"Bearer {settings.whatsapp_token}"
            ),
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {
                "body": message
            }
        }

        response = requests.post(
            WhatsAppService._graph_url(),
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            return {
                "status_code": response.status_code,
                "text": response.text,
            }
