
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app.services.whatsapp_service import WhatsAppService

router = APIRouter()

# Verify Endpoint
@router.get("")
async def verify_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None,
):
    """
    Meta webhook verification endpoint.
    """
    if (
        hub_mode == "subscribe"
        and hub_verify_token == wa.verify_token
    ):
        return PlainTextResponse(content=hub_challenge, status_code=200)

    return PlainTextResponse(
        content="Verification failed",
        status_code=403,
    )


@router.post("")
async def receive_message(request: Request):
    """
    Receive WhatsApp webhook events.
    """
    try:
        data = await request.json()

        # Let PyWa process the webhook
        WhatsAppService.handle_webhook(data)

        return JSONResponse(
            status_code=200,
            content={"status": "success"},
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
            },
        )