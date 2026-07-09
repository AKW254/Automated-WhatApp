import hmac
import hashlib
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.concurrency import run_in_threadpool

from app.services.whatsapp_service import WhatsAppService
from app.config.settings import settings
from app.utils.logger import logger

router = APIRouter()

#Verify Endpoint
@router.get("")
async def verify_webhook(request: Request):
    """Verify webhook endpoint for Meta/WhatsApp webhook subscription.
    
    Meta sends verification requests with query parameters:
    - hub.mode=subscribe
    - hub.verify_token=<token>
    - hub.challenge=<challenge>
    """
    # Extract query parameters - Meta uses dots in parameter names
    query_params = request.query_params
    
    hub_mode = query_params.get("hub.mode")
    hub_verify_token = query_params.get("hub.verify_token")
    hub_challenge = query_params.get("hub.challenge")
    
    logger.debug(
        f"Webhook verification request received. "
        f"Query params: {dict(query_params)}"
    )
    
    expected_token = settings.whatsapp_verify_token

    if not expected_token:
        logger.error(
            "WHATSAPP_VERIFY_TOKEN is not configured; "
            "Meta webhook verification cannot succeed."
        )
        return PlainTextResponse(
            content="Webhook verify token is not configured",
            status_code=500,
        )

    # Validate all required parameters are present
    if not all([hub_mode, hub_verify_token, hub_challenge]):
        logger.warning(
            f"Missing webhook verification parameters: "
            f"hub_mode={hub_mode}, hub_verify_token={'***' if hub_verify_token else None}, "
            f"hub_challenge={hub_challenge}. "
            f"Received params: {dict(query_params)}"
        )
        return PlainTextResponse(
            content="Verification failed",
            status_code=403,
        )

    # Verify the token matches
    if (
        hub_mode == "subscribe"
        and hub_verify_token == expected_token
    ):
        logger.info("WhatsApp webhook verification successful")
        return PlainTextResponse(
            content=hub_challenge,
            status_code=200,
        )

    logger.warning(
        f"Webhook verification failed: "
        f"hub_mode={hub_mode} (expected 'subscribe'), "
        f"token_match={hub_verify_token == expected_token}"
    )
    return PlainTextResponse(
        content="Verification failed",
        status_code=403,
    )
def _verify_webhook_signature(body: bytes, signature: str | None, token: str) -> bool:
    """Verify the X-Hub-Signature header from Meta/WhatsApp webhook.
    
    Args:
        body: The raw request body as bytes
        signature: The X-Hub-Signature header value
        token: The whatsapp_token from settings
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not signature:
        logger.warning("Missing X-Hub-Signature header")
        return False
    
    try:
        # Signature format is "sha256=<hash>"
        if not signature.startswith("sha256="):
            logger.warning(f"Invalid signature format: {signature[:20]}...")
            return False
        
        expected_hash = hmac.new(
            token.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        provided_hash = signature.split("=")[1]
        
        # Use constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(expected_hash, provided_hash)
        
        if not is_valid:
            logger.warning("Webhook signature verification failed")
        
        return is_valid
    except Exception as e:
        logger.exception(f"Error verifying webhook signature: {e}")
        return False

# Getting Message 
@router.post("")
async def receive_message(
    request: Request,
):
    # Verify webhook signature for security
    signature = request.headers.get("X-Hub-Signature-256")
    body = await request.body()
    
    if not _verify_webhook_signature(body, signature, settings.whatsapp_token):
        logger.error("Webhook signature verification failed - rejecting request")
        return JSONResponse(
            status_code=403,
            content={
                "status": "error",
                "message": "Webhook signature verification failed",
            },
        )
    
    try:
        data = await request.json()
    except Exception as exc:
        logger.exception("Invalid WhatsApp webhook payload")
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": str(exc),
            },
        )

    try:
        if not isinstance(data, dict):
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Webhook payload must be a JSON object.",
                },
            )

        entries = data.get("entry", [])
        if not entries:
            return {"status": "ignored"}

        changes = entries[0].get("changes", [])
        if not changes:
            return {"status": "ignored"}

        value = changes[0].get("value", {})

        if "messages" not in value:
            return {"status": "ignored"}

        message = value["messages"][0]

        sender = message["from"]

        if message["type"] != "text":
            await run_in_threadpool(
                WhatsAppService.send_text_message,
                sender,
                "Please send a text message."
            )
            return {"status": "success"}

        user_message = (
            message["text"]["body"]
        )

        logger.info("%s: %s", sender, user_message)

        reply = (
            f"You said: {user_message}"
        )

        await run_in_threadpool(
            WhatsAppService.send_text_message,
            sender,
            reply,
        )

        return {"status": "success"}

    except Exception as e:
        logger.exception("Failed to process WhatsApp message")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
            },
        )
        
