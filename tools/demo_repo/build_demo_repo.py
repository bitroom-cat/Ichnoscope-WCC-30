#!/usr/bin/env python3
"""Automated builder for the ichnoscope-demo-app repository.

Constructs a standalone git repository with an engineered 14-commit history
and 5 realistic defects without any fake markers (# BUG, # planted).
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def load_authors(config_path: Path) -> dict[str, dict[str, str | bool]]:
    """Load author configurations and refuse to run if placeholders exist."""
    if not config_path.is_file():
        raise RuntimeError(f"Authors configuration file not found at: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        authors = json.load(f)

    placeholders = []
    for dev_id, data in authors.items():
        for field in ("name", "email"):
            val = str(data.get(field, ""))
            if val == "REPLACE_ME" or not val.strip():
                placeholders.append(f"{dev_id}.{field}")

    if placeholders:
        print("[ERROR] Cannot build demo repository. Placeholder values found in authors.json:")
        for p in placeholders:
            print(f"  • {p}")
        print("\nPlease update tools/demo_repo/authors.json with real GitHub accounts before building.")
        sys.exit(1)

    return authors


def run_git(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> str:
    """Execute git command and return standard output."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    res = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        env=full_env,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def write_file(dest: Path, content: str) -> None:
    """Write string to file ensuring LF line endings."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Ensure LF endings regardless of host OS
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    with open(dest, "w", encoding="utf-8", newline="\n") as f:
        f.write(normalized)


class DemoRepoBuilder:
    """Constructs the synthetic demo repository history."""

    def __init__(self, target_dir: Path, authors: dict[str, dict[str, str | bool]], now_dt: datetime.datetime):
        self.target = target_dir
        self.authors = authors
        self.now = now_dt
        self.commit_shas: list[str] = []

    def commit(self, author_key: str, offset_delta: datetime.timedelta, message: str) -> str:
        """Create a git commit with engineered author and committer dates."""
        dev = self.authors[author_key]
        commit_dt = self.now - offset_delta
        iso_date = commit_dt.isoformat()

        env = {
            "GIT_AUTHOR_NAME": str(dev["name"]),
            "GIT_AUTHOR_EMAIL": str(dev["email"]),
            "GIT_AUTHOR_DATE": iso_date,
            "GIT_COMMITTER_NAME": str(dev["name"]),
            "GIT_COMMITTER_EMAIL": str(dev["email"]),
            "GIT_COMMITTER_DATE": iso_date,
        }

        run_git(["add", "-A"], cwd=self.target)
        run_git(["commit", "-m", message], cwd=self.target, env=env)
        sha = run_git(["rev-parse", "HEAD"], cwd=self.target)
        self.commit_shas.append(sha)
        print(f"  [{len(self.commit_shas):02d}] {sha[:7]} ({iso_date[:19]}) @{dev['name']}: {message}")
        return sha

    def build(self) -> None:
        """Execute the 14-stage commit pipeline."""
        print(f"\n[BUILD] Initializing repository at {self.target}...")
        self.target.mkdir(parents=True, exist_ok=True)

        run_git(["init", "-b", "main"], cwd=self.target)
        run_git(["config", "core.autocrlf", "false"], cwd=self.target)
        run_git(["config", "commit.gpgSign", "false"], cwd=self.target)

        scratch_src = Path(__file__).resolve().parent / "scratch_app"

        # ---------------------------------------------------------
        # Commit 1: NOW - 30d (dev_a) Initial scaffold
        # ---------------------------------------------------------
        write_file(self.target / ".gitattributes", "* text=auto eol=lf\n")
        write_file(self.target / ".gitignore", "__pycache__/\n*.py[cod]\n*$py.class\n.pytest_cache/\n.coverage\nhtmlcov/\n.env\n.venv/\nenv/\nvenv/\ncaptured/\n*.log\n")
        write_file(self.target / "requirements.txt", "flask>=3.0.0\nsentry-sdk[flask]>=2.0.0\npytest>=8.0.0\n")
        write_file(self.target / "README.md", (scratch_src / "README.md").read_text(encoding="utf-8"))
        write_file(self.target / "observability.py", (scratch_src / "observability.py").read_text(encoding="utf-8"))
        write_file(self.target / "app.py", (scratch_src / "app.py").read_text(encoding="utf-8"))
        if (scratch_src / "templates" / "index.html").is_file():
            write_file(self.target / "templates" / "index.html", (scratch_src / "templates" / "index.html").read_text(encoding="utf-8"))
        write_file(self.target / "routes" / "__init__.py", '"""HTTP Blueprint route definitions for customer API services."""\n')
        write_file(self.target / "services" / "__init__.py", '"""Business logic and external domain service packages."""\n')
        self.commit("dev_a", datetime.timedelta(days=30), "Initial scaffold: Flask app structure and config")

        # ---------------------------------------------------------
        # Commit 2: NOW - 28d (dev_a) Cart service (total_price is written here, correct for dict)
        # In commit 2, get_cart returns empty dict for unknown carts so .items() never fails
        # ---------------------------------------------------------
        cart_c2 = (scratch_src / "services" / "cart.py").read_text(encoding="utf-8")
        # In early safe version, get_cart returned {} for missing cart
        cart_c2_safe = cart_c2.replace("return ACTIVE_CARTS.get(cart_id)", "return ACTIVE_CARTS.get(cart_id, {})")
        write_file(self.target / "services" / "cart.py", cart_c2_safe)
        write_file(self.target / "routes" / "cart.py", (scratch_src / "routes" / "cart.py").read_text(encoding="utf-8"))
        self.commit("dev_a", datetime.timedelta(days=28), "Add cart service and total calculation endpoint")

        # ---------------------------------------------------------
        # Commit 3: NOW - 25d (dev_b) Payment service & checkout route (safe version)
        # Safe version uses payload.get("stripe_token") and checks validity
        # ---------------------------------------------------------
        pay_c3 = (scratch_src / "services" / "payment.py").read_text(encoding="utf-8")
        pay_c3_safe = pay_c3.replace(
            '    token = payload["stripe_token"]',
            '    token = payload.get("stripe_token")\n    if not token:\n        raise PaymentError("Missing required card payment token")',
        )
        write_file(self.target / "services" / "payment.py", pay_c3_safe)
        write_file(self.target / "routes" / "checkout.py", (scratch_src / "routes" / "checkout.py").read_text(encoding="utf-8"))
        self.commit("dev_b", datetime.timedelta(days=25), "Implement payment processing and checkout workflow")

        # ---------------------------------------------------------
        # Commit 4: NOW - 21d (dev_c) Inventory service (safe) and supplier_feed.csv (numeric quantities only)
        # ---------------------------------------------------------
        feed_c4 = "sku,name,quantity,vendor,lead_days\nSKU-IN-STOCK,Ergonomic Office Chair,45,FurniCorp,3\nSKU-WIRELESS-MOUSE,Precision Wireless Mouse,80,TechLogistics,2\nSKU-DESK-MAT,Leather Desk Blotter,25,CraftStudio,5\nSKU-BACKORDER,Solid Walnut Standing Desk,0,NordicWood,14\n"
        write_file(self.target / "data" / "supplier_feed.csv", feed_c4)
        write_file(self.target / "services" / "inventory.py", (scratch_src / "services" / "inventory.py").read_text(encoding="utf-8"))
        write_file(self.target / "routes" / "inventory.py", (scratch_src / "routes" / "inventory.py").read_text(encoding="utf-8"))
        self.commit("dev_c", datetime.timedelta(days=21), "Add inventory service with supplier feed integration")

        # ---------------------------------------------------------
        # Commit 5: NOW - 18d (dev_b) Shipping service (safe, guards against zero weight)
        # ---------------------------------------------------------
        ship_c5 = (scratch_src / "services" / "shipping.py").read_text(encoding="utf-8")
        ship_c5_safe = ship_c5.replace(
            "    rate_factor = 1000 / weight_kg",
            "    effective_weight = max(weight_kg, 0.5)\n    rate_factor = 1000 / effective_weight",
        )
        write_file(self.target / "services" / "shipping.py", ship_c5_safe)
        write_file(self.target / "routes" / "shipping.py", (scratch_src / "routes" / "shipping.py").read_text(encoding="utf-8"))
        self.commit("dev_b", datetime.timedelta(days=18), "Add shipping rate quote service and route")

        # ---------------------------------------------------------
        # Commit 6: NOW - 15d (dev_a) Discounts service (safe, guards against empty list)
        # ---------------------------------------------------------
        disc_c6 = (scratch_src / "services" / "discounts.py").read_text(encoding="utf-8")
        disc_c6_safe = disc_c6.replace(
            "    best_discount = valid_matches[0]",
            '    if not valid_matches:\n        return {"applied_code": None, "discount_type": "none", "discount_amount_cents": 0, "new_subtotal_cents": order_subtotal_cents}\n    best_discount = valid_matches[0]',
        )
        write_file(self.target / "services" / "discounts.py", disc_c6_safe)
        write_file(self.target / "routes" / "discounts.py", (scratch_src / "routes" / "discounts.py").read_text(encoding="utf-8"))
        self.commit("dev_a", datetime.timedelta(days=15), "Add promotional discount code service")

        # ---------------------------------------------------------
        # Commit 7: NOW - 12d (dev_b) Happy-path test suite
        # ---------------------------------------------------------
        write_file(self.target / "tests" / "__init__.py", "")
        write_file(self.target / "tests" / "test_happy_paths.py", (scratch_src / "tests" / "test_happy_paths.py").read_text(encoding="utf-8"))
        write_file(self.target / "scripts" / "trigger_bug.py", (scratch_src / "scripts" / "trigger_bug.py").read_text(encoding="utf-8"))
        write_file(self.target / "scripts" / "capture_local.py", (scratch_src / "scripts" / "capture_local.py").read_text(encoding="utf-8"))
        self.commit("dev_b", datetime.timedelta(days=12), "Add automated happy-path test suite")

        # ---------------------------------------------------------
        # Commit 8: NOW - 8d (dev_a) Bug 5 introduced: discount lookup drops empty-list guard
        # ---------------------------------------------------------
        write_file(self.target / "services" / "discounts.py", (scratch_src / "services" / "discounts.py").read_text(encoding="utf-8"))
        self.commit("dev_a", datetime.timedelta(days=8), "Refactor discount lookup for tiered vouchers")

        # ---------------------------------------------------------
        # Commit 9: NOW - 6d (dev_b) Bug 2 root cause: get_cart returns None instead of {}
        # total_price is untouched from Commit 2
        # ---------------------------------------------------------
        write_file(self.target / "services" / "cart.py", (scratch_src / "services" / "cart.py").read_text(encoding="utf-8"))
        self.commit("dev_b", datetime.timedelta(days=6), "Update cart lookup to return None for missing carts")

        # ---------------------------------------------------------
        # Commit 10: NOW - 4d (dev_b) Bug 4 introduced: shipping quote drops zero-weight guard
        # ---------------------------------------------------------
        write_file(self.target / "services" / "shipping.py", (scratch_src / "services" / "shipping.py").read_text(encoding="utf-8"))
        self.commit("dev_b", datetime.timedelta(days=4), "Optimize shipping calculation formulae")

        # ---------------------------------------------------------
        # Commit 11: NOW - 2d (dev_c) Bug 3 introduced: supplier CSV includes row with N/A
        # ---------------------------------------------------------
        feed_c11 = (scratch_src / "data" / "supplier_feed.csv").read_text(encoding="utf-8")
        write_file(self.target / "data" / "supplier_feed.csv", feed_c11)
        self.commit("dev_c", datetime.timedelta(days=2), "Update supplier CSV format with vendor status")

        # ---------------------------------------------------------
        # Commit 12: NOW - 1d (dev_a) Documentation and docstring refresh
        # ---------------------------------------------------------
        readme_c12 = (scratch_src / "README.md").read_text(encoding="utf-8") + "\n<!-- Verified storefront deployment -->\n"
        write_file(self.target / "README.md", readme_c12)
        self.commit("dev_a", datetime.timedelta(days=1), "Update API documentation and route docstrings")

        # ---------------------------------------------------------
        # Commit 13: NOW - 20m (dev_a) Bug 1 introduced: payment reads payload["stripe_token"]
        # Line 84 becomes token = payload["stripe_token"]
        # ---------------------------------------------------------
        # First write without decoy comment
        pay_c13 = (scratch_src / "services" / "payment.py").read_text(encoding="utf-8")
        # In commit 13, below line 84 we don't have the decoy comment
        pay_c13_pre_decoy = pay_c13.replace(
            '        "receipt": receipt,\n        "created_at": now,\n    }',
            '        "receipt": receipt,\n    }',
        )
        write_file(self.target / "services" / "payment.py", pay_c13_pre_decoy)
        self.commit("dev_a", datetime.timedelta(minutes=20), "Streamline card charge token extraction")

        # ---------------------------------------------------------
        # Commit 14: NOW - 12m (dev_b) Decoy commit touching services/payment.py strictly BELOW line 84
        # ---------------------------------------------------------
        write_file(self.target / "services" / "payment.py", (scratch_src / "services" / "payment.py").read_text(encoding="utf-8"))
        self.commit("dev_b", datetime.timedelta(minutes=12), "Refine payment log messages and telemetry hints")

        print(f"\n[DONE] Successfully created 14 commits in {self.target} at HEAD={self.commit_shas[-1][:7]}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build synthetic ichnoscope-demo-app repository.")
    parser.add_argument(
        "--target",
        default=str(Path(__file__).resolve().parents[3] / "ichnoscope-demo-app"),
        help="Target demo repository directory (default: ../ichnoscope-demo-app)",
    )
    parser.add_argument(
        "--authors",
        default=str(Path(__file__).resolve().parent / "authors.json"),
        help="Path to authors.json",
    )
    parser.add_argument(
        "--now",
        help="Reference timestamp for NOW in ISO format (default: current system UTC time)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete and recreate target repository if it already exists",
    )

    args = parser.parse_args()
    target_path = Path(args.target).resolve()
    authors_path = Path(args.authors).resolve()

    if target_path.exists():
        if not args.force:
            print(f"[ERROR] Target directory already exists: {target_path}")
            print("Use --force to delete and recreate the repository.")
            return 1
        print(f"[CLEAN] Removing existing target at {target_path}...")
        shutil.rmtree(target_path, ignore_errors=True)

    authors = load_authors(authors_path)

    if args.now:
        now_dt = datetime.datetime.fromisoformat(args.now)
    else:
        now_dt = datetime.datetime.now(datetime.timezone.utc)

    builder = DemoRepoBuilder(target_path, authors, now_dt)
    builder.build()
    return 0


if __name__ == "__main__":
    sys.exit(main())
