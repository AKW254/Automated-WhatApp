from app.services import whatsapp_service as whatsapp_service_module


class DummyResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"status": "ok"}


def test_send_text_message_uses_access_token_for_graph_api(monkeypatch):
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return DummyResponse()

    monkeypatch.setattr(whatsapp_service_module.requests, "post", fake_post)
    monkeypatch.setattr(whatsapp_service_module.settings, "whatsapp_token", "access-token", raising=False)
    monkeypatch.setattr(whatsapp_service_module.settings, "whatsapp_phone_number_id", "12345", raising=False)
    monkeypatch.setattr(whatsapp_service_module.settings, "whatsapp_verify_token", "verify-token", raising=False)

    whatsapp_service_module.WhatsAppService.send_text_message("+254700000000", "hello")

    assert captured["headers"]["Authorization"] == "Bearer access-token"
    assert captured["url"].endswith("/12345/messages")
    assert captured["json"]["to"] == "+254700000000"
