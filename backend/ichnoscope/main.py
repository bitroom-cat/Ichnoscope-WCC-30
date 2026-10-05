"""FastAPI webhook gateway and service entrypoint for Ichnoscope."""

import hashlib
import hmac
import json
import logging

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from ichnoscope.api import router as api_router
from ichnoscope.config import get_settings
from ichnoscope.pipeline import run_pipeline

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ichnoscope Incident Triage Gateway",
    description="Autonomous incident triage correlating production crashes with git history.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


def verify_signature(body: bytes, signature: str | None, secret: str | None) -> bool:
    """Verify Sentry webhook HMAC-SHA256 signature using constant-time comparison."""
    if not secret:
        # If no secret is configured, reject signature verification
        return False
    if not signature:
        return False

    key = secret.encode("utf-8")
    expected = hmac.new(key, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.get("/healthz")
def healthz() -> dict[str, bool]:
    """Health check endpoint for container probes and uptime monitors."""
    return {"ok": True}


@app.post("/webhook/sentry")
async def sentry_webhook(
    request: Request,
    bg: BackgroundTasks,
    sentry_hook_signature: str | None = Header(default=None),
) -> dict[str, str]:
    """Receive Sentry error event webhook, verify HMAC signature, and trigger triage."""
    body = await request.body()
    settings = get_settings()

    secret = settings.sentry_client_secret.get_secret_value() if settings.sentry_client_secret else None
    if not verify_signature(body, sentry_hook_signature, secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    # Enqueue background task and reply 200 immediately
    bg.add_task(run_pipeline, payload)
    return {"status": "accepted"}
