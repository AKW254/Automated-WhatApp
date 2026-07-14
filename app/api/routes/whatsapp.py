import logging
from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, JSONResponse

from app.config.settings import settings
from app.utils.whatsapp import wa

# Set up logging
logger = logging.getLogger("uvicorn.error")

router = APIRouter()


@router.get("")
async def verify(request: Request):
    # Retrieve query parameters directly from the raw request object
    query_params = request.query_params
    
    hub_mode = query_params.get("hub.mode")
    hub_verify_token = query_params.get("hub.verify_token")
    hub_challenge = query_params.get("hub.challenge")

    # Log incoming parameters to help you debug mismatches
    logger.info(f"Webhook Verification Attempt - mode: {hub_mode}")
    logger.info(f"Received hub_verify_token: '{hub_verify_token}'")
    logger.info(f"Expected whatsapp_verify_token: '{settings.whatsapp_verify_token}'")

    if (
        hub_mode == "subscribe"
        and hub_verify_token == settings.whatsapp_verify_token
        and settings.whatsapp_verify_token is not None  # Ensure it is not None
    ):
        logger.info("Verification Successful!")
        # Meta expects ONLY the raw challenge value returned as plain text
        return PlainTextResponse(hub_challenge)

    logger.warning("Verification Failed: Token mismatch or invalid mode.")
    return PlainTextResponse(
        "Verification failed",
        status_code=403,
    )


@router.post("")
async def webhook(request: Request):
    try:
        wa.handle_webhook(await request.json())
        return {"status": "ok"}

    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(exc),
            },
        )