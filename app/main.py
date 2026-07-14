from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Config & Core
from app.config.settings import settings
#from app.config.database import init_db
# Add Middleware Register
from app.middleware.middlewareregister import register_middleware

# WhatsApp (pywa) client + webhook registration
from app.utils.whatsapp import init_whatsapp

#Logger (optional but recommended)
from app.utils.logger import logger

#App Initialization
def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Whatsapp Bot",
        version="1.0.0",
        description="AI Whatsapp Bot"
    )
    init_whatsapp(app)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom Middleware
    register_middleware(app)



     # Startup Event
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting up the application...")
        # Initialize database connection
        #await init_db()
        logger.info(
            f"WHATSAPP_VERIFY_TOKEN is {'set' if settings.whatsapp_verify_token else 'MISSING'}"
        )
                                                    
    
    #Root Route
    @app.get("/",tags=["Root"])
    def root():
        return {"message": "Welcome to the AI Whatsapp Bot API!"}
    #Health Check Route
    @app.get("/health",tags=["Health"])
    def health_check():
        return {"status": "healthy"}    
    return app
    

#app instance
app = create_app()