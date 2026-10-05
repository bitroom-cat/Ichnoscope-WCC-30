#!/usr/bin/env python3
"""Execute endpoint scenario requests against the Flask service."""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app

TRIGGERS = {
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


def trigger(scenario_id: str) -> None:
    """Send request triggering the requested scenario."""
    if scenario_id not in TRIGGERS:
        print(f"Unknown scenario '{scenario_id}'. Available: {list(TRIGGERS.keys())}")
        sys.exit(1)

    app = create_app()
    app.testing = True
    client = app.test_client()

    cfg = TRIGGERS[scenario_id]
    print(f"Triggering '{scenario_id}' -> {cfg['method']} {cfg['path']}")

    try:
        if cfg["method"] == "POST":
            resp = client.post(cfg["path"], json=cfg.get("json", {}))
        else:
            resp = client.get(cfg["path"])
        print(f"Response status: {resp.status_code}")
    except Exception as exc:  # noqa: BLE001
        print(f"Exception raised as expected: {type(exc).__name__}: {exc}")
        tb = traceback.format_exc()
        print(tb)
        # Re-raise so caller or verifier inspects full traceback
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/trigger_bug.py <payment|cart|inventory|shipping|discounts>")
        sys.exit(1)
    trigger(sys.argv[1].lower())
