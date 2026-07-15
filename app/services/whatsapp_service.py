class WhatsAppService:

    @staticmethod
    def process_message(client, msg):
        response = (
            "👋 Hello!\n\n"
            "Thank you for contacting us.\n"
            "One of our assistants will be with you shortly."
        )

        msg.reply_text(response)