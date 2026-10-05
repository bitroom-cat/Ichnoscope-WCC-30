"""Inventory fulfillment routes verifying stock levels and reserving SKUs."""

from flask import Blueprint, jsonify, request

from services.inventory import InventoryError, reserve_stock

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.post("/inventory/reserve")
def reserve_inventory_endpoint():
    """Reserve warehouse units for a specified product SKU code.

    Expected JSON payload:
        {
            "sku": "SKU-IN-STOCK",
            "quantity": 2
        }
    """
    payload = request.get_json(silent=True) or {}
    sku = payload.get("sku")
    if not sku:
        return jsonify({"error": "Missing required 'sku' field"}), 400

    quantity = int(payload.get("quantity", 1))

    try:
        reservation = reserve_stock(sku=sku, quantity=quantity)
        return jsonify(reservation), 200
    except InventoryError as exc:
        return jsonify({"error": str(exc)}), 404
