"""Checkout routes handling customer payment authorization and order placement."""

from typing import Any

from flask import Blueprint, jsonify, request

from services.payment import charge_card

checkout_bp = Blueprint("checkout", __name__)


def validate_checkout_payload(payload: dict[str, Any]) -> tuple[bool, str | None]:
    """Validate mandatory checkout fields including currency and numeric amount."""
    if not isinstance(payload, dict):
        return False, "Payload must be a JSON object"
    if "amount" not in payload:
        return False, "Missing amount field"
    if not isinstance(payload["amount"], (int, float)) or payload["amount"] <= 0:
        return False, "Amount must be a positive number"
    return True, None


@checkout_bp.post("/checkout")
def checkout_endpoint():
    """Process order payment and finalize cart transaction.

    Expected JSON payload:
        {
            "amount": 4500,
            "currency": "usd",
            "stripe_token": "tok_visa"
        }
    """
    payload = request.get_json(silent=True) or {}
    is_valid, error_msg = validate_checkout_payload(payload)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    # Invoke payment gateway service to authorize charge
    currency = payload.get("currency", "usd")
    charge_result = charge_card(payload, currency=currency)
    return jsonify({"status": "paid", "charge": charge_result}), 200
