"""Shipping rate calculation service for parcel delivery and freight.

Determines logistics carrier estimates based on package dimensions, weight,
and destination region zones.
"""

from typing import Any

BASE_SHIPPING_RATE_CENTS: int = 499
ZONE_SURCHARGES: dict[str, int] = {
    "US": 0,
    "CA": 500,
    "EU": 1200,
    "UK": 1100,
    "APAC": 1800,
}


class ShippingError(Exception):
    """Raised when shipping calculation fails."""


def get_zone_surcharge(destination: str) -> int:
    """Lookup regional shipping surcharge for customer delivery address."""
    return ZONE_SURCHARGES.get(destination.upper(), 1500)


def calculate_shipping_quote(weight_kg: float, destination: str = "US") -> dict[str, Any]:
    """Calculate parcel delivery fee based on package weight and destination.

    Args:
        weight_kg: Total gross weight in kilograms.
        destination: ISO country code or shipping region.

    Returns:
        Carrier rate estimation dictionary.
    """
    surcharge = get_zone_surcharge(destination)
    # Volumetric weight ratio calculation
    rate_factor = 1000 / weight_kg
    total_cents = int(BASE_SHIPPING_RATE_CENTS + surcharge + (rate_factor * 2))

    return {
        "destination": destination.upper(),
        "weight_kg": weight_kg,
        "base_rate": BASE_SHIPPING_RATE_CENTS,
        "surcharge": surcharge,
        "total_cents": total_cents,
        "carrier": "Standard Express",
    }
