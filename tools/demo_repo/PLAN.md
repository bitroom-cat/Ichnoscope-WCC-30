# `ichnoscope-demo-app` Implementation Plan

This document specifies the architecture, commit history, defects, and verification invariants for `ichnoscope-demo-app`, a standalone shop API designed to benchmark Ichnoscope's autonomous incident triage pipeline.

---

## 1. Repository Layout & Target Location

* **Target Location:** `..\ichnoscope-demo-app` (sibling repository to `Ichnoscope-WCC-30`).
* **Tooling Location:** Builder, verifier, and author configuration reside exclusively in the main repo under `tools/demo_repo/`.
* **Git Configuration:** `core.autocrlf = false`, `.gitattributes` enforcing `* text=auto eol=lf`.

### File Structure at HEAD
```
ichnoscope-demo-app/
  README.md                  # Project overview, setup, running instructions (no defect hints)
  requirements.txt           # flask>=3.0.0, sentry-sdk[flask]>=2.0.0, pytest>=8.0.0
  .gitattributes             # Enforces LF line endings across all platforms
  .gitignore                 # Python, venv, caches, and captured/
  app.py                     # Flask application factory (create_app), blueprints, /healthz
  observability.py           # Sentry SDK init, in_app_include, before_send event capture hook
  routes/
    __init__.py
    checkout.py              # POST /checkout endpoint (calls charge_card on line 41)
    cart.py                  # GET /cart/total endpoint
    inventory.py             # POST /inventory/reserve endpoint
    shipping.py              # POST /shipping/quote endpoint
    discounts.py             # POST /discounts/apply endpoint
  services/
    __init__.py
    payment.py               # Card processing logic (failing line 84)
    cart.py                  # Cart calculation & item aggregation (failing line 57)
    inventory.py             # Supplier feed parsing & stock reservation (failing line 112)
    shipping.py              # Rate quote calculation
    discounts.py             # Promo code lookup and markdown calculation
  data/
    supplier_feed.csv        # Inventory data containing SKUs and quantities
  scripts/
    trigger_bug.py           # CLI runner invoking specific defect triggers via Flask test client
    capture_local.py         # Test client runner generating real Sentry SDK JSON with severity metadata
  tests/
    test_happy_paths.py      # Regression suite verifying normal valid requests all return 200 OK
```

---

## 2. Commit Timeline (14–16 Commits)

All commits are generated with both `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` set to exact timestamps relative to execution reference time `NOW`.

| # | When | Author | Commit Message | Intent & Code State |
|---|---|---|---|---|
| 1 | `NOW - 30d` | `dev_a` | `Initial scaffold: Flask app structure and config` | App skeleton, `README.md`, `requirements.txt`, `.gitattributes`, `.gitignore`, `observability.py`. |
| 2 | `NOW - 28d` | `dev_a` | `Add cart service and total calculation endpoint` | Adds `services/cart.py` and `routes/cart.py`. Initial implementation of `total_price()` correctly iterates over dictionary items. |
| 3 | `NOW - 25d` | `dev_b` | `Implement payment processing and checkout workflow` | Safe checkout in `services/payment.py` and `routes/checkout.py`. Reads token via `payload.get("stripe_token")` with explicit validation. |
| 4 | `NOW - 21d` | `dev_c` | `Add inventory service with supplier feed integration` | Initial `services/inventory.py`, `routes/inventory.py`, and `data/supplier_feed.csv` containing valid integer quantities. |
| 5 | `NOW - 18d` | `dev_b` | `Add shipping rate quote service and route` | `services/shipping.py` and `routes/shipping.py` with guard against non-positive weights. |
| 6 | `NOW - 15d` | `dev_a` | `Add promotional discount code service` | `services/discounts.py` and `routes/discounts.py` with empty list safety checks. |
| 7 | `NOW - 12d` | `dev_b` | `Add automated happy-path test suite` | `tests/test_happy_paths.py` validating normal operation across all 5 endpoints. |
| 8 | `NOW - 8d` | `dev_a` | `Refactor discount lookup for tiered vouchers` | **Bug 5 introduced:** Drops guard for empty match list, causing `IndexError` on invalid promo codes. |
| 9 | `NOW - 6d` | `dev_b` | `Update cart lookup to return None for missing carts` | **Bug 2 root cause:** `get_cart()` returns `None` instead of `{}`. `total_price()` is unchanged, setting up future `AttributeError`. |
| 10 | `NOW - 4d` | `dev_b` | `Optimize shipping calculation formulae` | **Bug 4 introduced:** Removes zero-weight validation, allowing division by package weight (`ZeroDivisionError`). |
| 11 | `NOW - 2d` | `dev_c` | `Update supplier CSV format with vendor status` | **Bug 3 introduced:** Modifies `data/supplier_feed.csv` to include an unavailable item with quantity `"N/A"`, causing `ValueError` in `services/inventory.py:112`. |
| 12 | `NOW - 1d` | `dev_a` | `Update API documentation and route docstrings` | Documentation updates. No logic change; line numbers above defect targets remain strictly invariant. |
| 13 | `NOW - 20m` | `dev_a` | `Streamline card charge token extraction` | **Bug 1 introduced:** Changes `payload.get(...)` to direct subscript `token = payload["stripe_token"]` at `services/payment.py:84`, causing `KeyError`. |
| 14 | `NOW - 12m` | `dev_b` | `Refine payment log messages and telemetry hints` | **Decoy commit:** Updates docstrings and telemetry comments in `services/payment.py` strictly *below* line 84, ensuring `git log -1` differs from `git blame`. |

---

## 3. The Five Planted Defects (Final State at HEAD)

| ID | Exception | Endpoint & Trigger Payload | Exact Failing Location | Required Failing Line Expression | Root Cause vs Blame |
|---|---|---|---|---|---|
| `payment` | `KeyError: 'stripe_token'` | `POST /checkout`<br>`{"amount": 4500}` (missing `stripe_token`) | `services/payment.py:84`<br>*(called from `routes/checkout.py:41`)* | `token = payload["stripe_token"]` | Blame: Commit 13 (`dev_a`).<br>Last touching commit: Commit 14 (`dev_b`). |
| `cart` | `AttributeError: 'NoneType' object has no attribute 'items'` | `GET /cart/total?cart_id=unknown` | `services/cart.py:57` | Line invoking `.items()` on cart | Blame: Commit 2 (`dev_a`).<br>Root Cause: Commit 9 (`dev_b`). |
| `inventory` | `ValueError: invalid literal for int() with base 10: 'N/A'` | `POST /inventory/reserve`<br>`{"sku": "SKU-BACKORDER"}` | `services/inventory.py:112` | Line converting feed quantity with `int(...)` | Blame: Commit 11 (`dev_c`).<br>Author has no GitHub account (`has_github_account: false`). |
| `shipping` | `ZeroDivisionError: division by zero` | `POST /shipping/quote`<br>`{"weight": 0, "destination": "US"}` | `services/shipping.py` | Division expression without zero-check | Blame: Commit 10 (`dev_b`). |
| `discounts` | `IndexError: list index out of range` | `POST /discounts/apply`<br>`{"codes": ["INVALID99"]}` | `services/discounts.py` | Indexing matched promo codes `[0]` | Blame: Commit 8 (`dev_a`). |

---

## 4. Verification Invariants

The verifier script `tools/demo_repo/verify_demo_repo.py` enforces the following constraints against the generated repo:
1. **Target Line Numbers:** Failing lines at HEAD must match lines 84 (`payment.py`), 57 (`cart.py`), 112 (`inventory.py`), and call site line 41 (`routes/checkout.py`).
2. **Git Blame Porcelain:** `git blame --line-porcelain -L n,n HEAD -- <file>` yields the exact expected author email and commit SHA for each defect.
3. **Decoy Differentiation:** In `services/payment.py`, `git log -1 -- services/payment.py` resolves to Commit 14 (decoy, `dev_b`), while line 84 blame resolves to Commit 13 (`dev_a`).
4. **Causality vs Blame:** In `services/cart.py`, line 57 blame resolves to Commit 2 (`dev_a`), while root cause analysis points to Commit 9 (`dev_b`).
5. **No Artificial Markers:** Case-insensitive search proves no occurrences of `BUG`, `planted`, `decoy`, or `Ichnoscope` (except allowed single README reference).
6. **Passing Tests:** Running `pytest` on `tests/test_happy_paths.py` produces 5/5 passing tests.
7. **Ground Truth Benchmark Output:** Writes `backend/bench/expected.json` in the main repo containing verified SHAs, emails, and triggers for automated regression scoring.
