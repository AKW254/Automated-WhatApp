import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.utils.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        start_time = time.time()

        try:

            response = await call_next(request)

        except Exception as e:

            logger.error(f"Unhandled error: {str(e)}")

            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error"
                }
            )

        process_time = time.time() - start_time

        request_target = request.url.path
        if request.url.query:
            request_target = f"{request_target}?{request.url.query}"

        logger.info(
            f"{request.method} {request_target} "
            f"Status: {response.status_code} "
            f"Time: {process_time:.4f}s"
        )

        response.headers["X-Process-Time"] = str(process_time)

        return response
