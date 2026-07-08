import time
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

RATE_LIMIT = {}
MAX_REQUESTS = 100
WINDOW_SECONDS = 60
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = (
            request.client.host
            if request.client and request.client.host
            else "unknown"
        )
        current_time = time.time()

        if client_ip not in RATE_LIMIT:
            RATE_LIMIT[client_ip] = []

        # Remove timestamps outside the window
        RATE_LIMIT[client_ip] = [timestamp for timestamp in RATE_LIMIT[client_ip] if current_time - timestamp < WINDOW_SECONDS]

        if len(RATE_LIMIT[client_ip]) >= MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"error": "Too Many Requests"}
            )

        RATE_LIMIT[client_ip].append(current_time)

        response: Response = await call_next(request)
        return response
  
