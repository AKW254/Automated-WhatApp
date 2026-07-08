from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Config & Core
from app.config.settings import settings
#from app.config.database import init_db
# Add Middleware Register
from app.middleware.middlewareregister import register_middleware
#Routes (import modules directly)
from app.api.routes.whatsapp import router as whatapp_router
#Logger (optional but recommended)
from app.utils.logger import logger

#App Initialization
def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Whatsapp Bot",
        version="1.0.0",
        description="AI Whatsapp Bot"
    )

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

    # Routes
    app.include_router(whatapp_router, prefix="/api/whatapp", tags=["Whatsapp"])

     # Startup Event
    @app.on_event("startup")
    async def startup_event():
         logger.info("Starting up the application...")
         # Initialize database connection
         #await init_db()
         logger.info("Application startup complete.")
    
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