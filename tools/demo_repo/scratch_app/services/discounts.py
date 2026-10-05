"""Discount code redemption and promotional markdown service.

Evaluates coupon vouchers, seasonal sale codes, and customer loyalty
credits against the active merchant discount catalog.
"""

from typing import Any

DISCOUNT_CATALOG: dict[str, dict[str, Any]] = {
    "WELCOME10": {"type": "percent", "value": 10, "description": "10% off entire order"},
    "SAVE20": {"type": "fixed", "value": 2000, "description": "$20 flat discount"},
    "FREESHIP": {"type": "shipping", "value": 100, "description": "Free standard shipping"},
}


class DiscountError(Exception):
    """Raised when promotional discounts cannot be applied."""


def find_matching_discounts(codes: list[str]) -> list[dict[str, Any]]:
    """Match provided voucher codes against verified promotional catalog.

    Args:
        codes: List of uppercase promo voucher strings.

    Returns:
        List of matching promotional rule definitions.
    """
    matched = []
    for c in codes:
        upper = c.strip().upper()
        if upper in DISCOUNT_CATALOG:
            matched.append({"code": upper, **DISCOUNT_CATALOG[upper]})
    return matched


def apply_discount_voucher(codes: list[str], order_subtotal_cents: int = 5000) -> dict[str, Any]:
    """Select and calculate discount deduction for the provided promotional codes.

    Args:
        codes: Customer provided coupon vouchers.
        order_subtotal_cents: Gross order value before discount.

    Returns:
        Applied discount summary object.
    """
    valid_matches = find_matching_discounts(codes)
    # Select primary active promotional voucher
    best_discount = valid_matches[0]

    discount_amount = 0
    if best_discount["type"] == "percent":
        discount_amount = (order_subtotal_cents * best_discount["value"]) // 100
    elif best_discount["type"] == "fixed":
        discount_amount = min(best_discount["value"], order_subtotal_cents)

    return {
        "applied_code": best_discount["code"],
        "discount_type": best_discount["type"],
        "discount_amount_cents": discount_amount,
        "new_subtotal_cents": order_subtotal_cents - discount_amount,
    }
