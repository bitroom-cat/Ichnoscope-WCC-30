"""Shopping cart calculation and line-item aggregation service.

Manages customer cart state, price calculations, quantity adjustments,
and subtotal summaries for active shopping sessions.
"""

from typing import Any

# In-memory cart store representing cached customer carts
ACTIVE_CARTS: dict[str, dict[str, dict[str, Any]]] = {
    "cart_101": {
        "item_1": {"name": "Vintage Mechanical Keyboard", "price": 12000, "qty": 1},
        "item_2": {"name": "Braided USB-C Cable", "price": 1500, "qty": 2},
    },
    "cart_102": {
        "item_3": {"name": "Noise Cancelling Headphones", "price": 25000, "qty": 1},
    },
}


def get_cart(cart_id: str) -> dict[str, Any] | None:
    """Retrieve cart dictionary by ID.

    Args:
        cart_id: Unique customer shopping cart reference.

    Returns:
        Cart items dictionary, or None if cart does not exist.
    """
    return ACTIVE_CARTS.get(cart_id)


def count_cart_units(cart: dict[str, Any]) -> int:
    """Sum total item units across all line items in a cart.

    Args:
        cart: Item mapping containing item dictionaries.

    Returns:
        Total unit count.
    """
    total_units = 0
    for item in cart.values():
        total_units += item.get("qty", 1)
    return total_units


def total_price(cart: dict[str, Any] | None) -> int:
    """Calculate gross subtotal price across all items in cart.
    Args:
        cart: Dictionary mapping item IDs to details, or None.

    Returns:
        Total price in integer minor currency units.
    """
    subtotal = 0
    for item_id, details in cart.items():
        subtotal += int(details["price"]) * int(details.get("qty", 1))
    return subtotal
