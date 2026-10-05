"""Inventory service managing SKU reservations and vendor stock feed ingestion.

Coordinates warehouse replenishment checks against supplier catalog feeds
and maintains local stock reservation ledgers.
"""

import csv
from pathlib import Path
from typing import Any

DEFAULT_FEED_FILE: str = "supplier_feed.csv"


class InventoryError(Exception):
    """Raised when requested inventory cannot be reserved."""


def resolve_feed_path() -> Path:
    """Locate supplier CSV catalog feed file in the project data directory.

    Returns:
        Absolute Path to supplier feed CSV file.
    """
    base_dir = Path(__file__).resolve().parents[1]
    feed_path = base_dir / "data" / DEFAULT_FEED_FILE
    if not feed_path.is_file():
        feed_path = Path("data") / DEFAULT_FEED_FILE
    return feed_path


def parse_vendor_row(row: dict[str, str]) -> dict[str, Any]:
    """Normalize supplier CSV data row into standardized inventory record.

    Args:
        row: Dictionary parsed from CSV line.

    Returns:
        Cleaned supplier inventory record.
    """
    return {
        "sku": row.get("sku", "").strip(),
        "name": row.get("name", "").strip(),
        "vendor": row.get("vendor", "").strip(),
        "lead_days": int(row.get("lead_days", 3)),
    }


def check_minimum_reorder_level(available_units: int, threshold: int = 5) -> bool:
    """Evaluate whether current warehouse stock requires distributor restock order.

    Args:
        available_units: Current verified physical inventory count.
        threshold: Safety stock reorder trigger point.

    Returns:
        True if stock level has fallen below safety buffer.
    """
    return available_units < threshold


def format_reservation_summary(sku: str, units: int, lead_time_days: int) -> dict[str, Any]:
    """Construct confirmation response for successful stock reservation.

    Args:
        sku: Stock keeping unit code.
        units: Number of units allocated.
        lead_time_days: Expected fulfillment window.

    Returns:
        Structured reservation confirmation dictionary.
    """
    return {
        "sku": sku,
        "units_reserved": units,
        "fulfillment_window_days": lead_time_days,
        "status": "reserved",
    }


def load_supplier_catalog() -> list[dict[str, str]]:
    """Read and parse raw vendor catalog feed entries from CSV.

    Returns:
        List of raw catalog item records.
    """
    path = resolve_feed_path()
    records: list[dict[str, str]] = []
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def reserve_stock(sku: str, quantity: int = 1) -> dict[str, Any]:
    """Verify availability in supplier feed and reserve requested inventory units.

    Args:
        sku: Unique stock identifier code.
        quantity: Quantity of units to reserve (default: 1).

    Returns:
        Reservation confirmation object.

    Raises:
        InventoryError: If SKU is missing or insufficient units available.
        ValueError: If supplier quantity cannot be parsed as an integer.
    """
    catalog = load_supplier_catalog()
    for item in catalog:
        if item.get("sku") == sku:
            available_qty = int(item["quantity"])
            if available_qty < quantity:
                raise InventoryError(f"Insufficient stock for {sku}: requested {quantity}, available {available_qty}")
            return format_reservation_summary(sku, quantity, int(item.get("lead_days", 3)))

    raise InventoryError(f"SKU '{sku}' not found in supplier catalog")
