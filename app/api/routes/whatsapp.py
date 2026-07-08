from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import PlainTextResponse

from app.services.whatsapp_service import WhatsAppService
from app.config.settings import settings

router = APIRouter(
    prefix="/webhook",
    tags=["WhatsApp"]
)
#Verify Endpoint
@router.get("")
async def verify_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None,
):

    if (
        hub_mode == "subscribe"
        and hub_verify_token
        == settings.jwt_secret_key
    ):
        return PlainTextResponse(
            content=hub_challenge,
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
    data = await request.json()

    print(data)

    try:
        changes = data["entry"][0]["changes"][0]
        value = changes["value"]

        if "messages" not in value:
            return {
                "status": "ignored"
            }

        message = value["messages"][0]

        sender = message["from"]

        if message["type"] != "text":
            WhatsAppService.send_text_message(
                sender,
                "Please send a text message."
            )
            return {
                "status": "success"
            }

        user_message = (
            message["text"]["body"]
        )

        print(
            f"{sender}: {user_message}"
        )

        reply = (
            f"You said: {user_message}"
        )

        WhatsAppService.send_text_message(
            sender,
            reply,
        )

        return {
            "status": "success"
        }

    except Exception as e:
        print(e)

        return {
            "status": "error",
            "message": str(e)
        }
        