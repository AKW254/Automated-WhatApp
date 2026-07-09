import hashlib
import hmac
from urllib.parse import parse_qsl

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.concurrency import run_in_threadpool

from app.config.settings import settings
from app.services.whatsapp_service import WhatsAppService
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


def _verify_webhook_signature(
    body: bytes,
    signature: str | None,
    app_secret: str | None,
) -> bool:
    """Verify the X-Hub-Signature-256 header from Meta/WhatsApp webhook."""
    if not app_secret:
        logger.warning(
            "WHATSAPP_APP_SECRET is not configured; "
            "skipping webhook signature verification for this request."
        )
        return True

    if not signature:
        logger.warning("Missing X-Hub-Signature-256 header")
        return False

    try:
        if not signature.startswith("sha256="):
            logger.warning("Invalid signature format: %s...", signature[:20])
            return False

        expected_hash = hmac.new(
            app_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        provided_hash = signature.split("=", 1)[1]

        is_valid = hmac.compare_digest(expected_hash, provided_hash)
        if not is_valid:
            logger.warning("Webhook signature verification failed")

        return is_valid
    except Exception as exc:
        logger.exception("Error verifying webhook signature: %s", exc)
        return False


@router.get("", response_class=PlainTextResponse)
async def verify_webhook(request: Request):
    """Verify webhook endpoint for Meta/WhatsApp webhook subscription."""
    query_params = _extract_webhook_query_params(request)

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
        "Webhook verification request received. URL: %s, Query params: %s",
        request.url,
        safe_query_params,
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

    if not all([hub_mode, hub_verify_token, hub_challenge]):
        logger.warning(
            "Missing webhook verification parameters: "
            "hub_mode=%s, hub_verify_token=%s, hub_challenge=%s. "
            "Received params: %s",
            hub_mode,
            "***" if hub_verify_token else None,
            hub_challenge,
            safe_query_params,
        )
        return PlainTextResponse(
            content="Verification failed",
            status_code=403,
        )

    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("WhatsApp webhook verification successful")
        return PlainTextResponse(
            content=hub_challenge,
            status_code=200,
        )

    logger.warning(
        "Webhook verification failed: hub_mode=%s (expected 'subscribe'), token_match=%s",
        hub_mode,
        hub_verify_token == expected_token,
    )
    return PlainTextResponse(
        content="Verification failed",
        status_code=403,
    )


@router.post("")
async def receive_message(request: Request):
    signature = request.headers.get("X-Hub-Signature-256")
    body = await request.body()

    if not _verify_webhook_signature(
        body,
        signature,
        settings.whatsapp_app_secret,
    ):
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
        messages = value.get("messages") or []
        if not messages:
            return {"status": "ignored"}

        message = messages[0]
        sender = message["from"]
        message_type = message.get("type", "unknown")
        user_message = (message.get("text") or {}).get("body", "")

        if user_message:
            logger.info("%s: %s", sender, user_message)
        else:
            logger.info(
                "Received WhatsApp message from %s with type %s",
                sender,
                message_type,
            )

        reply = "Thanks for contacting us."

        await run_in_threadpool(
            WhatsAppService.send_text_message,
            sender,
            reply,
        )

        return {"status": "success"}

    except Exception as exc:
        logger.exception("Failed to process WhatsApp message")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(exc),
            },
        )
