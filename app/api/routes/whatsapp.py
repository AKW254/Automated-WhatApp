from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.concurrency import run_in_threadpool

from app.services.whatsapp_service import WhatsAppService
from app.config.settings import settings
from app.utils.logger import logger

router = APIRouter()
#Verify Endpoint
@router.get("")
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    expected_token = settings.whatsapp_verify_token or settings.jwt_secret_key

    if (
        hub_mode == "subscribe"
        and hub_verify_token == expected_token
    ):
        return PlainTextResponse(
            content=hub_challenge or "",
            status_code=200,
        )

    return PlainTextResponse(
        content="Verification failed",
        status_code=403,
    )
 #Getting Message 
@router.post("")
async def receive_message(
    request: Request,
):
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
        
