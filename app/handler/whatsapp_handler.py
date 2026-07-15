from pywa import filters
from pywa.types import Message

from app.utils.whatsapp import get_wa
from app.services.whatsapp_service import WhatsAppService

wa = get_wa()


@wa.on_message(filters.text)
def handle_message(client, msg: Message):
    WhatsAppService.process_message(client, msg)