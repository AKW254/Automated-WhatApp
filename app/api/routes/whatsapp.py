from fastapi import APIRouter
from pywa import WhatsApp, filters
from pywa.types import Message

from app.config.settings import settings
from app.utils.logger import logger

router = APIRouter()

# Initialize PyWa directly on our FastAPI APIRouter.
# PyWa automatically mounts the GET (verification) and POST (incoming payload)
# endpoints directly at the root of this router (""). No manual routes needed!
wa = WhatsApp(
    phone_id=settings.whatsapp_phone_number_id,
    token=settings.whatsapp_token,
    verify_token=settings.whatsapp_verify_token,
    app_secret=settings.whatsapp_app_secret,
    server=router,
    webhook_endpoint="/api/webhook",  # Matches the prefix of this router ("/api/webhook")
)


# Filter for only text messages to prevent handling media errors
@wa.on_message(filters.text)
def handle_text_message(client: WhatsApp, msg: Message):
    """
    Automatically triggers when a user sends a text message.
    """
    user_message = msg.text or ""
    sender_id = msg.from_user.wa_id
    sender_name = msg.from_user.name or "User"

    logger.info(f"Received message from {sender_name} ({sender_id}): {user_message}")

    # Static reply (Can be replaced with your AI model generator later)
    reply = (
        "Hello! Thank you for contacting us. "
        "Our AI assistant is processing your message."
    )

    # PyWa helper sends the response instantly back to the user
    msg.reply_text(text=reply)


@wa.on_message(~filters.text)
def handle_other_media(client: WhatsApp, msg: Message):
    """
    Fallback handler if a user sends a photo, voice note, document, etc.
    """
    logger.info(f"Received non-text message from {msg.from_user.wa_id}")
    msg.reply_text(text="Please send a text message.")