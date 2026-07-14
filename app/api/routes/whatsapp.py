from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from app.utils.whatsapp import wa

router = APIRouter()


@router.get("")
async def verify(request: Request):
    """Meta webhook verification."""
    return PlainTextResponse(
        wa.webhook_challenge_handler(request.query_params)
    )


@router.post("")
async def webhook(request: Request):
    """Receive webhook events from WhatsApp."""
    wa.handle_webhook(await request.json())
    return {"status": "ok"}