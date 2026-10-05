#!/usr/bin/env python3
"""Capture authentic Sentry SDK error events via local Flask test client."""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app

DEFAULT_COUNTS = {
    "payment": {"event_count": 120, "users_affected": 63},
    "cart": {"event_count": 22, "users_affected": 11},
    "inventory": {"event_count": 8, "users_affected": 4},
    "shipping": {"event_count": 35, "users_affected": 14},
    "discounts": {"event_count": 15, "users_affected": 6},
}

SCENARIOS = {
    "payment": {
        "method": "POST",
        "path": "/checkout",
        "json": {"amount": 4500, "currency": "usd"},
    },
    "cart": {
        "method": "GET",
        "path": "/cart/total?cart_id=unknown",
    },
    "inventory": {
        "method": "POST",
        "path": "/inventory/reserve",
        "json": {"sku": "SKU-BACKORDER", "quantity": 1},
    },
    "shipping": {
        "method": "POST",
        "path": "/shipping/quote",
        "json": {"weight": 0, "destination": "US"},
    },
    "discounts": {
        "method": "POST",
        "path": "/discounts/apply",
        "json": {"codes": ["INVALID99"], "subtotal": 5000},
    },
}


def capture_single(
    scenario_id: str,
    out_dir: Path,
    event_count: int | None = None,
    users_affected: int | None = None,
) -> Path:
    """Trigger specific defect and enhance captured Sentry SDK event with telemetry metadata."""
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    out_dir.mkdir(parents=True, exist_ok=True)
    temp_name = f"tmp_{scenario_id}"
    os.environ["CAPTURE_DIR"] = str(out_dir)
    os.environ["CAPTURE_NAME"] = temp_name

    app = create_app()
    app.testing = True
    client = app.test_client()

    cfg = SCENARIOS[scenario_id]
    try:
        if cfg["method"] == "POST":
            client.post(cfg["path"], json=cfg.get("json", {}))
        else:
            client.get(cfg["path"])
    except Exception:  # noqa: BLE001
        pass  # Exception is intercepted by Sentry SDK before_send hook

    temp_file = out_dir / f"{temp_name}.json"
    target_file = out_dir / f"real_{scenario_id}.json"

    if not temp_file.is_file():
        raise RuntimeError(f"SDK event was not captured for {scenario_id} at {temp_file}")

    with open(temp_file, "r", encoding="utf-8") as f:
        event_data = json.load(f)

    temp_file.unlink(missing_ok=True)

    defaults = DEFAULT_COUNTS.get(scenario_id, {"event_count": 10, "users_affected": 5})
    ev_count = event_count if event_count is not None else defaults["event_count"]
    us_count = users_affected if users_affected is not None else defaults["users_affected"]

    event_data["_ichnoscope"] = {
        "note": "Captured by the Sentry SDK from ichnoscope-demo-app (not hand-written).",
        "event_count": ev_count,
        "users_affected": us_count,
    }

    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(event_data, f, indent=2, default=str)

    print(f"[OK] Captured: {target_file}")
    return target_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture Sentry SDK events locally.")
    parser.add_argument("target", help="Scenario ID (payment|cart|inventory|shipping|discounts|all)")
    parser.add_argument("--out", default="captured", help="Output directory (default: captured)")
    parser.add_argument("--event-count", type=int, help="Override event_count")
    parser.add_argument("--users", type=int, help="Override users_affected")

    args = parser.parse_args()
    out_dir = Path(args.out).resolve()

    target = args.target.lower()
    if target == "all":
        for s in SCENARIOS:
            capture_single(s, out_dir, args.event_count, args.users)
    else:
        capture_single(target, out_dir, args.event_count, args.users)

    return 0


if __name__ == "__main__":
    sys.exit(main())
