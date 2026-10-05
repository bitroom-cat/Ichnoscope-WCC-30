"""Shipping calculation routes providing logistics fee quotes."""

from flask import Blueprint, jsonify, request

from services.shipping import calculate_shipping_quote

shipping_bp = Blueprint("shipping", __name__)


@shipping_bp.post("/shipping/quote")
def shipping_quote_endpoint():
    """Generate carrier delivery quote based on weight and country.

    Expected JSON payload:
        {
            "weight": 2.5,
            "destination": "US"
        }
    """
    payload = request.get_json(silent=True) or {}
    weight = float(payload.get("weight", 1.0))
    destination = payload.get("destination", "US")

    quote = calculate_shipping_quote(weight_kg=weight, destination=destination)
    return jsonify(quote), 200
