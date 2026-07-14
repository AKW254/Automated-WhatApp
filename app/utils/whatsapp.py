
from pywa import WhatsApp
from app.config.settings import settings

wa = WhatsApp(
    phone_id=settings.whatsapp_phone_number_id,
    token=settings.whatsapp_token,
    verify_token=settings.whatsapp_verify_token,
    app_secret=settings.whatsapp_app_secret,
)