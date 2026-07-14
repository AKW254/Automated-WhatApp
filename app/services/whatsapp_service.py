from pywa import WhatsApp
from pywa.types import Message

from app.utils.logger import logger


class WhatsAppService:
    @staticmethod
    def process_message(client: WhatsApp, msg: Message) -> None:
        """
        Process incoming WhatsApp messages.

        AI response generation will be implemented here later.
        """
        user_message = msg.text or ""

        logger.info(
            f"Message from {msg.from_user.wa_id}: {user_message}"
        )

        # TODO:
        # response = AIService.generate_response(
        #     user_id=msg.from_user.wa_id,
        #     message=user_message
        # )

        response = WhatsAppService.get_default_reply()

        msg.reply_text(response)

    @staticmethod
    def get_default_reply() -> str:
        """
        Temporary response until AI integration is implemented.
        """
        return (
            "Hello 👋\n\n"
            "Thank you for contacting us. "
            "Our AI assistant is currently processing your message "
            "and will respond shortly."
        )