from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse, JSONResponse

from app.config.settings import settings
from app.utils.whatsapp import wa

router = APIRouter()


@router.get("")
async def verify(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
):
    if (
        hub_mode == "subscribe"
        and hub_verify_token == settings.whatsapp_verify_token
    ):
        return PlainTextResponse(hub_challenge)

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