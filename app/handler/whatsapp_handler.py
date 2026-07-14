from pywa.types import Message

from app.utils.whatsapp import wa 
from app.services.whatsapp_service import WhatsAppService


@wa.on_message()
def handle_message(client, msg: Message):
    WhatsAppService.process_message(client, msg)