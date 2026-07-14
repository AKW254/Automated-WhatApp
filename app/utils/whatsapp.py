import logging
from typing import Optional

from fastapi import FastAPI
from pywa import WhatsApp, filters, types

from app.config.settings import settings

logger = logging.getLogger("uvicorn.error")

# Populated by init_whatsapp() once the FastAPI app exists.
# Import `wa` only from code that runs *after* init_whatsapp() has been called
# (e.g. inside request handlers) — not at module import time.
wa: Optional[WhatsApp] = None


def init_whatsapp(app: FastAPI) -> WhatsApp:
    """
    Create the pywa client and bind its webhook routes onto `app`.

    Call this once from your app factory / main.py, right after `app = FastAPI()`.
    pywa will auto-register GET (verification) and POST (incoming updates)
    handlers at `webhook_endpoint` — you no longer need a separate
    webhook.py router for this.
    """
    global wa

    wa = WhatsApp(
        phone_id=settings.whatsapp_phone_number_id,  # was whatsapp_phone_id (doesn't exist)
        token=settings.whatsapp_token,
        server=app,
        webhook_endpoint="/api/webhook",
        callback_url=settings.whatsapp_callback_url,
        verify_token=settings.whatsapp_verify_token,
        app_id=settings.whatsapp_app_id,
        app_secret=settings.whatsapp_app_secret,
    )

    # Import here (not at module top) to avoid a circular import with
    # whatsapp_service.py, which may in turn import things from this module.
    from app.services.whatsapp_service import WhatsAppService

    @wa.on_message(filters.text)
    def on_text(client: WhatsApp, msg: types.Message):
        WhatsAppService.process_message(client, msg)

    logger.info("WhatsApp webhook registered at /api/webhook")
    return wa