
from pywa import WhatsApp
from app.config.settings import settings

wa = WhatsApp(
    phone_id=settings.whatsapp_phone_id,
    token=settings.whatsapp_token,
    server=app,
    webhook_endpoint="/api/webhook",          # match wherever you want the route to live
    callback_url=settings.whatsapp_callback_url,   # public URL, no endpoint suffix
    verify_token=settings.whatsapp_verify_token,
    app_id=settings.whatsapp_app_id,
    app_secret=settings.whatsapp_app_secret,
)
