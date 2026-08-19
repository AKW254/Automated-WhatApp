from pywa import filters
from pywa.types import Message

from app.utils.whatsapp import get_wa
from app.services.whatsapp_service import WhatsAppService
from app.utils.logger import logger

wa = get_wa()


@wa.on_message(filters.text)
def handle_message(_, msg: Message):
    logger.info("========== TEXT MESSAGE ==========")
    logger.info(f"From: {msg.from_}")
    logger.info(f"Text: {msg.text}")
    logger.info("==================================")

    WhatsAppService.process_message(msg)