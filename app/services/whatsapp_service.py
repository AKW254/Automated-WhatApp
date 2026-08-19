from pywa.types import Message

from app.utils.logger import logger


class WhatsAppService:

    @staticmethod
    def process_message(msg: Message) -> None:
        try:
            logger.info(
                f"WhatsApp message from {msg.from_}: {msg.text}"
            )

            if msg.type == "text":
                response = (
                    "👋 Hello!\n\n"
                    "Thank you for contacting us.\n"
                    "One of our assistants will be with you shortly."
                )
            else:
                response = "Please send a text message."

            msg.reply_text(response)

            logger.info(
                f"Reply sent successfully to {msg.from_}"
            )

        except Exception as e:
            logger.error(
                f"WhatsApp processing error: {e}",
                exc_info=True
            )