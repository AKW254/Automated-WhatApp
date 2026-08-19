from typing import Optional
from fastapi import FastAPI
from pywa import WhatsApp
from app.config.settings import settings
from app.utils.logger import logger

wa: Optional[WhatsApp] = None


def init_whatsapp(app: FastAPI):
    """
    Initialize WhatsApp client with pywa library.
    
    Note: pywa will attempt to register the callback URL with Meta's API in a background thread.
    If this fails due to network issues, it won't block startup but will log the error.
    """
    global wa

    try:
        logger.info("Initializing WhatsApp client...")
        
        wa = WhatsApp(
            phone_id=settings.whatsapp_phone_number_id,
            token=settings.whatsapp_token,
            server=app,
            webhook_endpoint="/api/webhook",
            verify_token=settings.whatsapp_verify_token,
            )
        logger.info("WhatsApp client initialized successfully")
        logger.info(f"Webhook endpoint: /api/webhook")
        logger.info(f"Callback URL: {settings.whatsapp_callback_url}")
        
        return wa
    except Exception as e:
        logger.error(f"Failed to initialize WhatsApp client: {str(e)}", exc_info=True)
        raise


def get_wa() -> WhatsApp:
    """
    Get the global WhatsApp client instance.
    
    Raises:
        RuntimeError: If WhatsApp client was not initialized
    """
    if wa is None:
        logger.error("WhatsApp client is None - initialization may have failed")
        raise RuntimeError("WhatsApp client not initialized. Check initialization logs for details.")
    return wa