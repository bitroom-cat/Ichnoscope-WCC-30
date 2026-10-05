#!/usr/bin/env python3
"""Test utility to verify Sentry webhook ingestion via local FastAPI or public ngrok tunnel.

Usage:
    python backend/scripts/test_webhook_ping.py
    python backend/scripts/test_webhook_ping.py --url https://xxxx.ngrok-free.app/webhook/sentry
    python backend/scripts/test_webhook_ping.py --secret my-sentry-secret
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def detect_ngrok_url() -> str | None:
    """Query local ngrok client API to find the active public HTTPS URL."""
    try:
        req = urllib.request.Request("http://127.0.0.1:4040/api/tunnels", headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tunnels = data.get("tunnels", [])
            for t in tunnels:
                url = t.get("public_url", "")
                if url.startswith("https://"):
                    return f"{url}/webhook/sentry"
            if tunnels:
                return f"{tunnels[0].get('public_url')}/webhook/sentry"
    except Exception:  # noqa: BLE001
        return None
    return None


def get_default_secret() -> str | None:
    """Check environment or backend/.env for SENTRY_CLIENT_SECRET."""
    if "SENTRY_CLIENT_SECRET" in os.environ and os.environ["SENTRY_CLIENT_SECRET"].strip():
        return os.environ["SENTRY_CLIENT_SECRET"].strip()

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("SENTRY_CLIENT_SECRET="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val
    return None


def compute_signature(payload_bytes: bytes, secret: str) -> str:
    """Generate Sentry HMAC-SHA256 signature."""
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Send test webhook payload to Ichnoscope.")
    parser.add_argument(
        "--url",
        help="Target webhook URL (default: auto-detected ngrok or http://127.0.0.1:8000/webhook/sentry)",
    )
    parser.add_argument(
        "--secret",
        default=get_default_secret(),
        help="Sentry client secret for HMAC signing (default: reads from .env)",
    )
    parser.add_argument(
        "--fixture",
        default=str(Path(__file__).resolve().parents[1] / "fixtures" / "bug1_keyerror_payment.json"),
        help="Path to sample Sentry error fixture JSON",
    )
    args = parser.parse_args()

    # Determine target URL
    target_url = args.url
    if not target_url:
        ngrok_url = detect_ngrok_url()
        if ngrok_url:
            print(f"[OK] Auto-detected active ngrok tunnel: {ngrok_url}")
            target_url = ngrok_url
        else:
            target_url = "http://127.0.0.1:8000/webhook/sentry"
            print(f"[INFO] ngrok not detected; falling back to local: {target_url}")

    # Load fixture payload
    fixture_path = Path(args.fixture)
    if not fixture_path.is_file():
        print(f"[FAIL] Fixture file not found: {fixture_path}")
        return 1

    try:
        raw_content = fixture_path.read_text(encoding="utf-8")
        payload_data = json.loads(raw_content)
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] Failed to parse JSON from {fixture_path}: {exc}")
        return 1

    payload_bytes = json.dumps(payload_data).encode("utf-8")

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "sentry-webhook-test/1.0",
    }

    if args.secret:
        sig = compute_signature(payload_bytes, args.secret)
        headers["sentry-hook-signature"] = sig
        print(f"[AUTH] Computed HMAC-SHA256 signature: {sig[:12]}...")
    else:
        print("[AUTH] No SENTRY_CLIENT_SECRET provided. Sending raw unauthenticated request (dev bypass).")

    print(f"\n[SEND] Delivering webhook to {target_url} ({len(payload_bytes)} bytes)...")
    req = urllib.request.Request(target_url, data=payload_bytes, headers=headers, method="POST")

    start_time = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            duration = (time.perf_counter() - start_time) * 1000
            resp_body = resp.read().decode("utf-8")
            print(f"[PASS] HTTP {resp.status} in {duration:.1f}ms")
            print(f"       Response Body: {resp_body}")
            if resp.status == 200:
                print("\n==================================================================")
                print(" [SUCCESS] Webhook accepted by Ichnoscope backend!")
                print(" The triage pipeline has been triggered in the background.")
                print(" View triaged run in dashboard: http://localhost:3000/app/runs")
                print("==================================================================")
                return 0
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        print(f"[FAIL] Server responded with HTTP {exc.code}: {err_body}")
        if exc.code == 401:
            print("       Hint: HMAC signature verification failed. Verify your SENTRY_CLIENT_SECRET.")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] Connection error: {exc}")
        print("       Hint: Is FastAPI running? (run 'uvicorn ichnoscope.main:app --port 8000')")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
