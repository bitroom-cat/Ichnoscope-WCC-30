"""Observability and Sentry SDK telemetry initialization."""

import json
import os
import subprocess
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration


def resolve_release_identifier() -> str:
    """Resolve full 40-character git commit SHA for release tracking."""
    env_rel = os.environ.get("RELEASE", "").strip()
    if env_rel:
        return env_rel
    try:
        raw_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if len(raw_sha) == 40:
            return raw_sha
    except Exception:  # noqa: BLE001
        pass
    return "0000000000000000000000000000000000000000"


def _capture_hook(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Intercept error events and optionally mirror payload to local capture directory."""
    capture_dir = os.environ.get("CAPTURE_DIR")
    if capture_dir:
        out_dir = Path(capture_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        event_name = os.environ.get("CAPTURE_NAME", "captured_event")
        out_file = out_dir / f"{event_name}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(event, f, default=str, indent=2)
    return event


def init_observability() -> None:
    """Initialize Sentry SDK with Flask integration and custom in-app frame scopes."""
    dsn = os.environ.get("SENTRY_DSN", "")
    release = resolve_release_identifier()
    environment = os.environ.get("SENTRY_ENVIRONMENT", "production")

    sentry_sdk.init(
        dsn=dsn,
        release=release,
        environment=environment,
        integrations=[FlaskIntegration()],
        in_app_include=["app", "routes", "services"],
        before_send=_capture_hook,
        traces_sample_rate=1.0,
    )
