import requests

from app.config.settings import settings
from app.utils.logger import logger  # Reusing your logger for error visibility


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
    ) -> dict:
        headers = {
            "Authorization": f"Bearer {settings.whatsapp_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"body": message}
        }

        try:
            response = requests.post(
                WhatsAppService._graph_url(),
                headers=headers,
                json=payload,
                timeout=30
            )
            
          
            if not response.ok:
                try:
                    error_details = response.json()
                    logger.error(f"Meta API Error response: {error_details}")
                except ValueError:
                    logger.error(f"Meta API Error (Non-JSON): {response.text}")
            
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as exc:
            logger.exception("HTTP Request to WhatsApp Graph API failed")
            # Re-raise so the calling route or threadpool knows it failed
            raise exc