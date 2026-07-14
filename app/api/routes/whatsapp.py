from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, JSONResponse

from app.utils.whatsapp import wa

router = APIRouter()


@router.get("")
async def verify(
    hub_mode: str | None = None,
    hub_verify_token: str | None = None,
    hub_challenge: str | None = None,
):
    """
    Verify Meta WhatsApp webhook subscription.
    """
    try:
        challenge = wa.webhook_challenge_handler(
            vt=hub_verify_token,
            ch=hub_challenge,
        )
        return PlainTextResponse(challenge)

    except ValueError:
        return PlainTextResponse(
            "Verification failed",
            status_code=403,
        )


@router.post("")
async def webhook(request: Request):
    """
    Receive webhook events from Meta.
    """
    try:
        wa.handle_webhook(await request.json())

        return JSONResponse(
            status_code=200,
            content={"status": "ok"},
        )

    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(exc),
            },
        )