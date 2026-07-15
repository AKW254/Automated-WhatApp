from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
        logger.info("Starting up the application...")
        logger.info(
            "WHATSAPP_VERIFY_TOKEN is %s",
            "set" if settings.whatsapp_verify_token else "MISSING",
        )

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

    return fastapi_app

# Instantiate global "app" for ASGI servers to pick up
app = create_app()