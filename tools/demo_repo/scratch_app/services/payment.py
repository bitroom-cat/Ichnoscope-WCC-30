"""Payment gateway service handling transaction authorization and card charges.

Integrates with customer billing accounts to verify funding sources and
simulate credit card token capture in accordance with PCI DSS standards.
"""

import hashlib
import time
from typing import Any

SUPPORTED_CURRENCIES: tuple[str, ...] = ("usd", "eur", "gbp", "cad", "aud")
DEFAULT_TRANSACTION_FEE_BPS: int = 290  # 2.9%
FLAT_TRANSACTION_FEE_CENTS: int = 30   # $0.30


class PaymentError(Exception):
    """Raised when card processing cannot be completed."""


def calculate_processing_fee(amount_cents: int) -> int:
    """Calculate card network processing fee for a given gross transaction amount.

    Args:
        amount_cents: Total charge amount in integer minor units (e.g. cents).

    Returns:
        Fee in minor units rounded down to nearest integer.
    """
    variable_fee = (amount_cents * DEFAULT_TRANSACTION_FEE_BPS) // 10000
    return variable_fee + FLAT_TRANSACTION_FEE_CENTS


def generate_receipt_identifier(token: str, amount_cents: int, timestamp: float) -> str:
    """Construct unique transaction reference code based on payment signature.

    Args:
        token: Payment provider authorization token.
        amount_cents: Charge value in minor currency units.
        timestamp: Epoch timestamp of transaction execution.

    Returns:
        Alphanumeric receipt reference string.
    """
    raw_seed = f"{token}:{amount_cents}:{timestamp}".encode("utf-8")
    digest = hashlib.sha256(raw_seed).hexdigest()[:12]
    return f"rcpt_{digest}"


def verify_currency_support(currency: str) -> bool:
    """Check whether requested settlement currency is currently supported.

    Args:
        currency: ISO 4217 lowercase three-letter currency code.

    Returns:
        True if processing is enabled for this currency.
    """
    return currency.lower() in SUPPORTED_CURRENCIES


def parse_charge_metadata(payload: dict[str, Any]) -> dict[str, str]:
    """Extract customer metadata tags attached to checkout request.

    Args:
        payload: Unfiltered checkout JSON dictionary.

    Returns:
        Sanitized string key-value pairs for ledger auditing.
    """
    meta = payload.get("metadata")
    if isinstance(meta, dict):
        return {str(k): str(v) for k, v in meta.items()}
    return {}


def charge_card(payload: dict[str, Any], currency: str = "usd") -> dict[str, Any]:
    """Authorize and capture credit card charge for an order.

    Args:
        payload: Request payload containing payment parameters.
        currency: Target settlement currency code (default: 'usd').
    """
    amount = int(payload["amount"])
    token = payload["stripe_token"]
    if not verify_currency_support(currency):
        raise PaymentError(f"Unsupported currency: {currency}")

    now = time.time()
    receipt = generate_receipt_identifier(token, amount, now)
    fee = calculate_processing_fee(amount)

    return {
        "id": f"ch_{receipt}",
        "amount": amount,
        "currency": currency.lower(),
        "fee": fee,
        "captured": True,
        "receipt": receipt,
        "created_at": now,
    }
