"""Cart management routes for customer item aggregation and subtotal lookup."""

from flask import Blueprint, jsonify, request

from services.cart import count_cart_units, get_cart, total_price

cart_bp = Blueprint("cart", __name__)


@cart_bp.get("/cart/total")
def cart_total_endpoint():
    """Retrieve line item unit count and gross price total for a shopping cart.

    Query parameters:
        cart_id: Unique string cart identifier (e.g. 'cart_101').
    """
    cart_id = request.args.get("cart_id", "cart_101")
    cart_data = get_cart(cart_id)

    total_cents = total_price(cart_data)
    units = count_cart_units(cart_data) if cart_data else 0

    return jsonify({
        "cart_id": cart_id,
        "units": units,
        "total_cents": total_cents,
    }), 200
