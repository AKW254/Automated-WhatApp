import hmac
import hashlib
from urllib.parse import parse_qsl

from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.concurrency import run_in_threadpool

from app.services.whatsapp_service import WhatsAppService
from app.config.settings import settings
from app.utils.logger import logger

router = APIRouter()


def _verify_webhook_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    """Verify that the incoming webhook payload was signed by Meta using the App Secret."""
    if not signature or not app_secret:
        return False

    # Meta prefixes the header value with 'sha256='
    if signature.startswith("sha256="):
        signature = signature.replace("sha256=", "")

    # Calculate expected HMAC-SHA256 signature
    expected_signature = hmac.new(
        app_secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


def _extract_webhook_query_params(request: Request) -> dict[str, str]:
    """Return webhook verification query params from the request or proxy headers."""
    query_params = dict(request.query_params)
    if query_params:
        return query_params

    raw_query_string = request.scope.get("query_string", b"")
    if raw_query_string:
        parsed_query = dict(
            parse_qsl(
                raw_query_string.decode("utf-8", errors="ignore"),
                keep_blank_values=True,
            )
        )
        if parsed_query:
            return parsed_query

    # Some gateways forward the original URL in a header but strip the ASGI query string.
    for header_name in ("x-original-uri", "x-forwarded-uri", "x-rewrite-url"):
        forwarded_uri = request.headers.get(header_name)
        if not forwarded_uri or "?" not in forwarded_uri:
            continue

        forwarded_query = forwarded_uri.split("?", 1)[1]
        parsed_query = dict(parse_qsl(forwarded_query, keep_blank_values=True))
        if parsed_query:
            return parsed_query

    return {}


# Verify Endpoint
@router.get("", response_class=PlainTextResponse)
async def verify_webhook(request: Request):
    """Verify webhook endpoint for Meta/WhatsApp webhook subscription."""
    query_params = _extract_webhook_query_params(request)

    if not query_params:
        logger.info("Received empty GET request. Handled as a routine health check ping.")
        return PlainTextResponse(
            content="WhatsApp Webhook Endpoint is online and active.",
            status_code=200,
        )

    hub_mode = query_params.get("hub.mode") or query_params.get("hub_mode")
    hub_verify_token = (
        query_params.get("hub.verify_token") or query_params.get("hub_verify_token")
    )
    hub_challenge = (
        query_params.get("hub.challenge") or query_params.get("hub_challenge")
    )

    safe_query_params = dict(query_params)
    if "hub.verify_token" in safe_query_params:
        safe_query_params["hub.verify_token"] = "***"
    if "hub_verify_token" in safe_query_params:
        safe_query_params["hub_verify_token"] = "***"
    
    logger.debug(f"Webhook verification request received. Query params: {safe_query_params}")
    
    expected_token = settings.whatsapp_verify_token

    if not expected_token:
        logger.error("WHATSAPP_VERIFY_TOKEN is not configured.")
        return PlainTextResponse(
            content="Webhook verify token is not configured",
            status_code=500,
        )

    if not all([hub_mode, hub_verify_token, hub_challenge]):
        return PlainTextResponse(content="Verification failed", status_code=403)

    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("WhatsApp webhook verification successful")
        return PlainTextResponse(content=hub_challenge, status_code=200)

    return PlainTextResponse(content="Verification failed", status_code=403)


# Getting Message 
@router.post("")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    signature = request.headers.get("X-Hub-Signature-256")
    body = await request.body()
    app_secret = settings.whatsapp_app_secret
    
    # Temporarily set to True to bypass verification while debugging gateway headers
    bypass_verification = True 
    
    if not bypass_verification:
        if not app_secret or not _verify_webhook_signature(body, signature, app_secret):
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
            content={"status": "error", "message": str(exc)},
        )

    try:
        if not isinstance(data, dict):
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Webhook payload must be an object."},
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
          # The auto reply target string
        reply = "Thanks for contacting us."
        if message["type"] != "text":
            background_tasks.add_task(
                WhatsAppService.send_text_message,
                sender,
                reply
            )
            return {"status": "success"}

        user_message = message["text"]["body"]
        logger.info(f"Received message from {sender}: {user_message}")

        # The auto reply target string
        reply = "Thanks for contacting us."

        # Send response back via BackgroundTasks to instantly return 200 OK to Meta
        background_tasks.add_task(
            WhatsAppService.send_text_message,
            sender,
            reply,
        )

        return {"status": "success"}

    except Exception as e:
        logger.exception("Failed to process WhatsApp message")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)},
        )