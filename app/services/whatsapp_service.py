import requests

from app.config.settings import settings

class WhatsAppService:

    GRAPH_URL = (
        f"https://graph.facebook.com/v23.0/"
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
            WhatsAppService.GRAPH_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        print(response.json())

        return response.json()