from typing import Optional
from fastapi import FastAPI
from pywa import WhatsApp
from app.config.settings import settings

wa: Optional[WhatsApp] = None


def init_whatsapp(app: FastAPI):
    global wa

    wa = WhatsApp(
        phone_id=settings.whatsapp_phone_number_id,
        token=settings.whatsapp_token,
        server=app,
        webhook_endpoint="/api/webhook",
        callback_url=settings.whatsapp_callback_url,
        verify_token=settings.whatsapp_verify_token,
        app_id=settings.whatsapp_app_id,
        app_secret=settings.whatsapp_app_secret,
    )

    return wa


def get_wa() -> WhatsApp:
    if wa is None:
        raise RuntimeError("WhatsApp client not initialized.")
    return wa