# Sample Storefront Service

Sample e-commerce microservice application simulating order checkout, item carts, inventory reservations, shipping rate quotes, and discount redemptions for Ichnoscope evaluation.

## Getting Started

### Installation
```bash
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Service
```bash
python app.py
```
The service will start on port 5000. Verify readiness by requesting `http://localhost:5000/healthz`.

### Running Tests
```bash
pytest tests/
```

### Testing Endpoint Behavior
You can execute automated sample requests against the API endpoints using the CLI runners in `scripts/`:
```bash
python scripts/trigger_bug.py payment
python scripts/trigger_bug.py cart
python scripts/trigger_bug.py inventory
python scripts/trigger_bug.py shipping
python scripts/trigger_bug.py discounts
```
