from fastapi import FastAPI

from app.middleware.loggingMiddleware import LoggingMiddleware
from app.middleware.securityHeadersMiddleware import SecurityHeadersMiddleware
from app.middleware.ratelimitMiddleware import RateLimitMiddleware


from app.utils.logger import logger


def register_middleware(app: FastAPI):
    """
    Register all application middleware here.
    Order matters: first added = outermost layer
    """

    app.add_middleware(LoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)

    logger.info("Middleware registered successfully")