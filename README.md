# Agentic WhatsApp Bot

An automated WhatsApp messaging backend built with FastAPI and `pywa`. The system handles incoming WhatsApp webhooks and auto-responses, designed with an architecture ready for LangGraph agent integration.

---

## Directory Structure

```text
.
├── app/
│   ├── agents/          # AI agent logic and state processing (In Development)
│   ├── config/          # Environment variables and application settings
│   ├── graph/           # LangGraph flows and decision trees
│   ├── handlers/        # Event handlers and pywa message listeners
│   ├── middleware/      # Middleware registrations
│   ├── models/          # Data models
│   ├── schemas/         # Pydantic schema definitions
│   ├── services/        # Message processing business logic
│   ├── tasks/           # Background tasks
│   ├── tools/           # Custom agent execution tools
│   └── utils/           # WhatsApp client initializers and logging helpers
├── Dockerfile           # Deployment container setup
├── main.py              # Application entry point & FastAPI setup
└── requirements.txt     # Dependency specifications
```

---

## Prerequisites

Install and configure the following before starting:

* **[Python 3.10+](https://www.python.org/)**
* **[ngrok](https://ngrok.com/)** (or an alternative reverse proxy for local webhook testing)
* A **Meta for Developers Account** with an active WhatsApp Cloud API app setup.

---

## Run After Cloning

Clone the repository and navigate to the project root:

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 1. Configure Environment Variables

Create a `.env` file in the root directory:

```env
APP_NAME="AI Whatsapp Bot"
ENVIRONMENT="development"
DEBUG=true
LOG_LEVEL="INFO"

# Meta WhatsApp Cloud API Configuration
WHATSAPP_PHONE_NUMBER_ID="your_phone_number_id"
WHATSAPP_VERIFY_TOKEN="your_custom_verification_token"
WHATSAPP_APP_SECRET="your_app_secret"
WHATSAPP_TOKEN="your_system_user_access_token"
WHATSAPP_CALLBACK_URL="https://your-ngrok-subdomain.ngrok-free.app/wa/webhook"
```

### 2. Set Up Virtual Environment

Create and activate a Python virtual environment, then install required dependencies:

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Expose Local Webhook Server

Start `ngrok` in a separate terminal to expose port 8000 to the public internet:

```bash
ngrok http 8000
```

Copy the HTTPS forwarding address (e.g., `https://abc123.ngrok-free.app`) and set up your Meta Webhook URL:
* **Callback URL**: `https://abc123.ngrok-free.app/wa/webhook`
* **Verify Token**: Must match `WHATSAPP_VERIFY_TOKEN` in `.env`.

### 4. Run Application

Start the FastAPI development server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verify service status by visiting [http://localhost:8000/health](http://localhost:8000/health).

---

## Webhook Debugging & Troubleshooting

If webhooks are failing or incoming messages are not registering:

1. **Test Payload Logging**: Post raw sample JSON to the built-in debug endpoint (`/api/webhook/debug`) to confirm signature validation and logger activity:
   ```bash
   curl -X POST http://localhost:8000/api/webhook/debug \
     -H "Content-Type: application/json" \
     -d "{\"test\": \"payload\"}"
   ```
2. **Verify Meta Webhook Subscriptions**: Ensure the `messages` topic field is subscribed to inside your Meta Developer Dashboard under **WhatsApp > Configuration**.
3. **Verify Tokens**: Ensure `WHATSAPP_VERIFY_TOKEN` matches the exact string provided during Meta webhook setup.

---

## Configuration Reference

| Setting | Purpose |
| --- | --- |
| `WHATSAPP_PHONE_NUMBER_ID` | Phone ID assigned by Meta Business Manager. |
| `WHATSAPP_VERIFY_TOKEN` | Secret string for endpoint verification handshakes. |
| `WHATSAPP_APP_SECRET` | App Secret key used for webhook signature verification. |
| `WHATSAPP_TOKEN` | Access token for sending outbound WhatsApp Cloud API messages. |
| `WHATSAPP_CALLBACK_URL` | Public HTTPS callback URL where incoming messages are routed. |

---

## Useful Commands

```bash
# Start development server with hot-reload
uvicorn main:app --reload

# Start production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Run test suite
pytest
```

---

## Development Roadmap

- [x] Base FastAPI setup with CORS and error handlers.
- [x] `pywa` integration for incoming and outgoing WhatsApp messages.
- [ ] Raw webhook payload debug endpoints.
- [ ] Connect LangGraph agents (`app/graph` and `app/agents`) to process message contexts dynamically.
- [ ] Implement database persistence (`app/models`) for chat state and thread memory.
