from pywa import WhatsApp
from pywa.types import Message

from app.utils.whatsapp import wa
from app.utils.logger import logger


class WhatsAppService:
    @staticmethod
    def process_message(
        client: WhatsApp,
        msg: Message,
    ) -> None:
        """
        Handle incoming customer messages.

        AI logic will be implemented here later.
        """
        user_message = msg.text or ""

        logger.info(
            f"Message from {msg.from_user.wa_id}: {user_message}"
        )

        # TODO:
        # response = AIService.generate_response(
        #     user_id=msg.from_user.wa_id,
        #     message=user_message,
        # )

        response = (
            "👋 Hello!\n\n"
            "Thank you for contacting us. "
            "Our AI assistant is processing your message "
            "and will respond shortly."
        )

        msg.reply_text(response)