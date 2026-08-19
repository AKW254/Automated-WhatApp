from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json

from app.config.settings import settings
from app.middleware.middlewareregister import register_middleware
from app.utils.whatsapp import init_whatsapp
from app.utils.logger import logger

def create_app() -> FastAPI:
    # Rename 'app' to 'fastapi_app' to prevent name collision with the 'app' module import
    fastapi_app = FastAPI(
        title="AI Whatsapp Bot",
        version="1.0.0",
        description="AI Whatsapp Bot",
    )

    # CORS
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware
    register_middleware(fastapi_app)
    
    # Initialize WhatsApp and register webhook routes
    init_whatsapp(fastapi_app)

    # Import handlers AFTER WhatsApp has been initialized
    import app.handler.whatsapp_handler

    @fastapi_app.on_event("startup")
    async def startup_event():
        logger.info("=" * 60)
        logger.info("Starting up the application...")
        logger.info("=" * 60)
        
        # Log critical settings
        logger.info(f"App Name: {settings.app_name}")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug Mode: {settings.debug}")
        logger.info(f"Log Level: {settings.LOG_LEVEL}")
        
        # Log WhatsApp configuration
        logger.info(f"WhatsApp Phone ID: {settings.whatsapp_phone_number_id}")
        logger.info(f"WhatsApp Callback URL: {settings.whatsapp_callback_url}")
        logger.info(
            f"WHATSAPP_VERIFY_TOKEN: {'[OK]' if settings.whatsapp_verify_token else '[MISSING] (webhook verification may fail)'}"
        )
        logger.info(
            f"WHATSAPP_APP_SECRET: {'[OK]' if settings.whatsapp_app_secret else '[MISSING]'}"
        )
        logger.info(
            f"WHATSAPP_TOKEN: {'[OK]' if settings.whatsapp_token else '[MISSING]'}"
        )
        
        logger.info("=" * 60)
        logger.info("NOTE: pywa will register webhook URL with Meta API in background")
        logger.info("      If registration times out, incoming webhooks may still work")
        logger.info("      if your URL is already registered in Meta Business Manager")
        logger.info("=" * 60)

    @fastapi_app.get("/", tags=["Root"])
    async def root():
        return {
            "message": "Welcome to the AI Whatsapp Bot API!"
        }

    @fastapi_app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy"
        }

    # DEBUG: Add webhook logging endpoint to track incoming payloads
    @fastapi_app.post("/api/webhook/debug", tags=["Debug"])
    async def webhook_debug(request: Request):
        """Debug endpoint to log all incoming webhook payloads"""
        try:
            body = await request.body()
            payload = json.loads(body)
            logger.info(f"DEBUG WEBHOOK RECEIVED: {json.dumps(payload, indent=2)}")
            
            # Extract key info for debugging
            if "entry" in payload and payload["entry"]:
                entry = payload["entry"][0]
                if "changes" in entry and entry["changes"]:
                    change = entry["changes"][0]
                    if "value" in change:
                        value = change["value"]
                        if "messages" in value:
                            for msg in value["messages"]:
                                logger.info(f"Message from {msg.get('from')}: {msg.get('text', {}).get('body', 'N/A')}")
            
            return {"status": "debug_logged"}
        except Exception as e:
            logger.error(f"Debug webhook error: {str(e)}")
            return {"status": "error", "error": str(e)}

    return fastapi_app

# Instantiate global "app" for ASGI servers to pick up
app = create_app()