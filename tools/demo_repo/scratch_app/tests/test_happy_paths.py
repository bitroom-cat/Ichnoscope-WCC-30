"""Happy path regression tests verifying standard e-commerce workflows."""

import pytest
from app import create_app


@pytest.fixture
def client():
    """Create test client fixture for application testing."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_healthz(client):
    """Health check probe endpoint returns 200."""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json["status"] == "healthy"


def test_checkout_happy_path(client):
    """Valid checkout with card token succeeds."""
    payload = {
        "amount": 4500,
        "currency": "usd",
        "stripe_token": "tok_visa_valid",
    }
    resp = client.post("/checkout", json=payload)
    assert resp.status_code == 200
    data = resp.json
    assert data["status"] == "paid"
    assert data["charge"]["captured"] is True
    assert data["charge"]["amount"] == 4500


def test_cart_total_happy_path(client):
    """Known cart calculates positive total."""
    resp = client.get("/cart/total?cart_id=cart_101")
    assert resp.status_code == 200
    data = resp.json
    assert data["cart_id"] == "cart_101"
    assert data["units"] == 3
    assert data["total_cents"] == 15000


def test_inventory_reserve_happy_path(client):
    """Stock reservation succeeds for in-stock SKU."""
    payload = {
        "sku": "SKU-IN-STOCK",
        "quantity": 2,
    }
    resp = client.post("/inventory/reserve", json=payload)
    assert resp.status_code == 200
    data = resp.json
    assert data["sku"] == "SKU-IN-STOCK"
    assert data["units_reserved"] == 2
    assert data["status"] == "reserved"


def test_shipping_quote_happy_path(client):
    """Parcel shipping quote generates valid fee."""
    payload = {
        "weight": 2.5,
        "destination": "US",
    }
    resp = client.post("/shipping/quote", json=payload)
    assert resp.status_code == 200
    data = resp.json
    assert data["destination"] == "US"
    assert data["total_cents"] > 0


def test_discounts_apply_happy_path(client):
    """Valid promotional code applies discount."""
    payload = {
        "codes": ["WELCOME10"],
        "subtotal": 5000,
    }
    resp = client.post("/discounts/apply", json=payload)
    assert resp.status_code == 200
    data = resp.json
    assert data["applied_code"] == "WELCOME10"
    assert data["discount_amount_cents"] == 500
    assert data["new_subtotal_cents"] == 4500
