"""Promotional voucher redemption routes."""

from flask import Blueprint, jsonify, request

from services.discounts import apply_discount_voucher

discounts_bp = Blueprint("discounts", __name__)


@discounts_bp.post("/discounts/apply")
def apply_discounts_endpoint():
    """Apply discount voucher code to pending checkout subtotal.

    Expected JSON payload:
        {
            "codes": ["WELCOME10"],
            "subtotal": 5000
        }
    """
    payload = request.get_json(silent=True) or {}
    codes = payload.get("codes", [])
    subtotal = int(payload.get("subtotal", 5000))

    summary = apply_discount_voucher(codes=codes, order_subtotal_cents=subtotal)
    return jsonify(summary), 200
