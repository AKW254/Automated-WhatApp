from pywa import WhatsApp 
from pywa.types import Message
  
from app.config.settings import settings
from app.utils.logger import logger  # Reusing your logger for error visibility


class WhatsAppService:
    wa = WhatsApp(
    phone_id=settings.whatsapp_phone_number_id,
    token=settings.whatsapp_token,
    verify_token=settings.whatsapp_verify_token,
    app_secret=settings.whatsapp_app_secret,
)
    @wa.on_message()
    def handle_message(client:WhatsApp,msg: Message):
        user_message =  msg.text or ""
        logger.info(
            f"Message from {msg.from_user.wa_id}:{user_message}"
        )    
        # Replace with AI-generated response later
        reply = (
        "Hello! Thank you for contacting us. "
        "Our AI assistant is processing your message."
        )

        msg.reply_text(reply)