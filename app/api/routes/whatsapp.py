import hmac
import hashlib
from urllib.parse import parse_qsl

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.concurrency import run_in_threadpool

from app.services.whatsapp_service import WhatsAppService
from app.config.settings import settings
from app.utils.logger import logger

router = APIRouter()


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
    """Verify webhook endpoint for Meta/WhatsApp webhook subscription.
    
    Meta sends verification requests with query parameters:
    - hub.mode=subscribe
    - hub.verify_token=<token>
    - hub.challenge=<challenge>
    """
    query_params = _extract_webhook_query_params(request)

    # Handle empty query parameters gracefully (Health checks / Pings)
    if not query_params:
        logger.info("Received empty GET request. Handled as a routine health check ping.")
        return PlainTextResponse(
            content="WhatsApp Webhook Endpoint is online and active.",
            status_code=200,
        )

    hub_mode = query_params.get("hub.mode") or query_params.get("hub_mode")
    hub_verify_token = (
        query_params.get("hub.verify_token")
        or query_params.get("hub_verify_token")
    )
    hub_challenge = (
        query_params.get("hub.challenge")
        or query_params.get("hub_challenge")
    )

    safe_query_params = dict(query_params)
    if "hub.verify_token" in safe_query_params:
        safe_query_params["hub.verify_token"] = "***"
    if "hub_verify_token" in safe_query_params:
        safe_query_params["hub_verify_token"] = "***"
    
    logger.debug(
        f"Webhook verification request received. "
        f"URL: {request.url}, "
        f"Query params: {safe_query_params}"
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
            f"Received params: {safe_query_params}"
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


# Getting Message 
@router.post("")
async def receive_message(
    request: Request,
):
    # Verify webhook signature for security
    signature = request.headers.get("X-Hub-Signature-256")
    body = await request.body()
    
    # Assumes _verify_webhook_signature helper function is defined globally or imported
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

        user_message = message["text"]["body"]
        logger.info("%s: %s", sender, user_message)

        # 👇 UPDATED: Custom static reply as requested
        reply = "Thanks for contacting us."

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