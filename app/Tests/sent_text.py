import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
                
from app.services.whatsapp_service import WhatsAppService

try:
    result = WhatsAppService.send_text_message("254799155770", "test")
    print("Success:", result)
except Exception as e:
    print("Failed:", e)
