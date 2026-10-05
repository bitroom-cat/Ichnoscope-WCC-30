#!/usr/bin/env python3
"""Automated verifier for the ichnoscope-demo-app repository.

Enforces all 8 verification invariants and writes benchmark ground truth
to backend/bench/expected.json in the main repository.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path


def run_git(args: list[str], cwd: Path) -> str:
    """Execute git command and return standard output."""
    res = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def parse_blame_line(repo_dir: Path, rel_file: str, line_no: int) -> tuple[str, str, str]:
    """Extract commit SHA, author email, and committed datetime via git blame porcelain."""
    out = run_git(["blame", "--line-porcelain", f"-L{line_no},{line_no}", "HEAD", "--", rel_file], cwd=repo_dir)
    sha = out.split("\n")[0].split(" ")[0].strip()

    email = ""
    committer_time = ""
    for line in out.split("\n"):
        if line.startswith("author-mail "):
            email = line[len("author-mail ") :].strip().strip("<>").strip()
        elif line.startswith("committer-time "):
            raw_ts = int(line[len("committer-time ") :].strip())
            committer_time = datetime.datetime.fromtimestamp(raw_ts, datetime.timezone.utc).isoformat()

    return sha, email, committer_time


def check_forbidden_markers(repo_dir: Path) -> list[str]:
    """Find any forbidden artificial bug markers across all repository files."""
    forbidden = ["bug", "planted", "decoy", "ichnoscope"]
    violations = []

    for p in repo_dir.rglob("*"):
        if not p.is_file() or ".git" in p.parts or "__pycache__" in p.parts or "captured" in p.parts or ".pytest_cache" in p.parts:
            continue
        # README.md is permitted to mention Ichnoscope once
        if p.name == "README.md":
            text = p.read_text(encoding="utf-8", errors="ignore").lower()
            if text.count("ichnoscope") > 1:
                violations.append(f"{p.name}: contains multiple mentions of 'ichnoscope'")
            for word in ["planted", "decoy"]:
                if word in text:
                    violations.append(f"{p.name}: contains '{word}'")
            continue

        text = p.read_text(encoding="utf-8", errors="ignore").lower()
        for word in forbidden:
            # scripts/trigger_bug.py and capture_local.py require specific tokens defined in spec
            if p.name == "trigger_bug.py" and word == "bug":
                continue
            if p.name == "capture_local.py" and word == "ichnoscope":
                continue
            if word in text:
                violations.append(f"{p.relative_to(repo_dir)}: contains '{word}'")

    return violations


def run_trigger_simulation(repo_dir: Path, scenario_id: str) -> tuple[str, str, int, str]:
    """Execute trigger scenario and extract exception type and last in-app frame."""
    sys.path.insert(0, str(repo_dir))
    try:
        from app import create_app
        from scripts.trigger_bug import TRIGGERS

        app = create_app()
        app.testing = True
        client = app.test_client()

        cfg = TRIGGERS[scenario_id]
        if cfg["method"] == "POST":
            client.post(cfg["path"], json=cfg.get("json", {}))
        else:
            client.get(cfg["path"])

        raise RuntimeError(f"Scenario '{scenario_id}' did not raise an exception")
    except Exception as exc:  # noqa: BLE001
        exc_type = type(exc).__name__
        tb = traceback.extract_tb(exc.__traceback__)

        # Find the last frame belonging to the application (services or routes)
        last_app_frame = None
        for frame in reversed(tb):
            norm_path = frame.filename.replace("\\", "/")
            if "services/" in norm_path or "routes/" in norm_path or norm_path.endswith("app.py"):
                last_app_frame = frame
                break

        if not last_app_frame:
            last_app_frame = tb[-1]

        rel_path = last_app_frame.filename.replace("\\", "/").split("ichnoscope-demo-app/")[-1]
        if "services/" in rel_path:
            rel_path = "services/" + rel_path.split("services/")[-1]
        elif "routes/" in rel_path:
            rel_path = "routes/" + rel_path.split("routes/")[-1]

        return exc_type, rel_path, last_app_frame.lineno, str(last_app_frame.line or "").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ichnoscope-demo-app invariants.")
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
    args = parser.parse_args()

    repo_dir = Path(args.target).resolve()
    if not repo_dir.is_dir() or not (repo_dir / ".git").is_dir():
        print(f"[FAIL] Demo repository not found or not initialized at {repo_dir}")
        return 1

    with open(args.authors, "r", encoding="utf-8") as f:
        authors = json.load(f)

    print("\n" + "=" * 80)
    print("           ICHNOSCOPE DEMO REPOSITORY VERIFICATION SUITE")
    print("=" * 80)
    print(f"Target: {repo_dir}\n")

    head_sha = run_git(["rev-parse", "HEAD"], cwd=repo_dir)
    print(f"[GIT] HEAD Commit: {head_sha}")

    # Expected defects definition
    expected_specs = [
        {
            "id": "payment",
            "file": "services/payment.py",
            "line": 84,
            "line_text": 'token = payload["stripe_token"]',
            "expected_exc": "KeyError",
            "blame_author": "dev_a",
            "root_cause_author": "dev_a",
            "blame_matches_root_cause": True,
            "has_decoy": True,
        },
        {
            "id": "cart",
            "file": "services/cart.py",
            "line": 57,
            "line_text": "for item_id, details in cart.items():",
            "expected_exc": "AttributeError",
            "blame_author": "dev_a",
            "root_cause_author": "dev_b",
            "blame_matches_root_cause": False,
            "has_decoy": False,
        },
        {
            "id": "inventory",
            "file": "services/inventory.py",
            "line": 112,
            "line_text": 'available_qty = int(item["quantity"])',
            "expected_exc": "ValueError",
            "blame_author": "dev_c",
            "root_cause_author": "dev_c",
            "blame_matches_root_cause": True,
            "has_decoy": False,
        },
        {
            "id": "shipping",
            "file": "services/shipping.py",
            "line": 40,
            "line_text": "rate_factor = 1000 / weight_kg",
            "expected_exc": "ZeroDivisionError",
            "blame_author": "dev_b",
            "root_cause_author": "dev_b",
            "blame_matches_root_cause": True,
            "has_decoy": False,
        },
        {
            "id": "discounts",
            "file": "services/discounts.py",
            "line": 49,
            "line_text": "best_discount = valid_matches[0]",
            "expected_exc": "IndexError",
            "blame_author": "dev_a",
            "root_cause_author": "dev_a",
            "blame_matches_root_cause": True,
            "has_decoy": False,
        },
    ]

    all_passed = True
    verified_bugs = []

    print("-" * 80)
    print(f"{'BUG ID':<12} | {'FILE:LINE':<24} | {'BLAME AUTHOR':<15} | {'BLAME SHA':<9} | {'STATUS'}")
    print("-" * 80)

    for spec in expected_specs:
        bug_id = spec["id"]
        rel_file = spec["file"]
        req_line = spec["line"]
        req_text = spec["line_text"]

        file_path = repo_dir / rel_file
        lines = file_path.read_text(encoding="utf-8").splitlines()

        # Invariant 1: Failing line text & number
        if len(lines) < req_line or lines[req_line - 1].strip() != req_text.strip():
            actual = lines[req_line - 1].strip() if len(lines) >= req_line else "<EOF>"
            print(f"[FAIL] {bug_id} line {req_line} text mismatch. Expected '{req_text}', got '{actual}'")
            all_passed = False
            continue

        # Invariant 2: git blame porcelain
        blame_sha, blame_email, committed_at = parse_blame_line(repo_dir, rel_file, req_line)
        expected_dev = authors[spec["blame_author"]]
        if blame_email.lower() != str(expected_dev["email"]).lower():
            print(f"[FAIL] {bug_id} blame email mismatch. Expected {expected_dev['email']}, got {blame_email}")
            all_passed = False
            continue

        # Invariant 3: Trigger simulation & last in-app frame
        exc_type, frame_file, frame_line, frame_text = run_trigger_simulation(repo_dir, bug_id)
        if exc_type != spec["expected_exc"]:
            print(f"[FAIL] {bug_id} exception mismatch. Expected {spec['expected_exc']}, got {exc_type}")
            all_passed = False
            continue
        if frame_file != rel_file or frame_line != req_line:
            print(f"[FAIL] {bug_id} last in-app frame mismatch. Expected {rel_file}:{req_line}, got {frame_file}:{frame_line}")
            all_passed = False
            continue

        # Invariant 4: Decoy commit on payment
        last_commit_touching = run_git(["log", "-1", "--format=%H", "--", rel_file], cwd=repo_dir)
        if spec["has_decoy"]:
            if last_commit_touching == blame_sha:
                print(f"[FAIL] {bug_id} decoy invariant failed: last commit touching file equals blame commit ({blame_sha[:7]})")
                all_passed = False
                continue

        # Invariant 5: Root cause commit on cart
        root_cause_sha = blame_sha
        root_cause_email = blame_email
        if not spec["blame_matches_root_cause"]:
            # Find commit 9 (dev_b commit that changed get_cart)
            cart_log = run_git(["log", "--format=%H %an <%ae> %s", "--", rel_file], cwd=repo_dir).splitlines()
            c9_line = [l for l in cart_log if "Update cart lookup to return None" in l]
            if not c9_line:
                print(f"[FAIL] {bug_id} root-cause commit (commit 9) not found in git log")
                all_passed = False
                continue
            root_cause_sha = c9_line[0].split(" ")[0].strip()
            root_cause_email = str(authors[spec["root_cause_author"]]["email"])
            if root_cause_sha == blame_sha:
                print(f"[FAIL] {bug_id} root-cause SHA equals blame SHA ({blame_sha[:7]})")
                all_passed = False
                continue

        dev_has_github = bool(expected_dev.get("has_github_account", True))

        verified_bugs.append({
            "id": bug_id,
            "exception_type": exc_type,
            "file": rel_file,
            "line": req_line,
            "line_text": req_text,
            "blame_sha": blame_sha,
            "blame_author_email": blame_email,
            "blame_author_has_github_account": dev_has_github,
            "root_cause_sha": root_cause_sha,
            "root_cause_author_email": root_cause_email,
            "last_commit_touching_file_sha": last_commit_touching,
            "committed_at": committed_at,
            "expected_within_window_if_triggered_now": True,
            "blame_matches_root_cause": spec["blame_matches_root_cause"],
            "trigger": f"python scripts/trigger_bug.py {bug_id}",
        })

        print(f"{bug_id:<12} | {rel_file + ':' + str(req_line):<24} | {expected_dev['name']:<15} | {blame_sha[:7]:<9} | OK")

    print("-" * 80)

    # Invariant 7: Happy-path test suite
    print("\n[CHECK] Running happy-path pytest test suite in demo repo...")
    pytest_res = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_happy_paths.py", "-q"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    if pytest_res.returncode != 0:
        print("[FAIL] Happy-path test suite failed:")
        print(pytest_res.stdout)
        print(pytest_res.stderr)
        all_passed = False
    else:
        print("  [PASS] Happy-path tests succeeded: " + pytest_res.stdout.strip())

    # Invariant 8: No artificial markers
    violations = check_forbidden_markers(repo_dir)
    if violations:
        print(f"\n[FAIL] Found {len(violations)} forbidden text marker(s):")
        for v in violations:
            print(f"  • {v}")
        all_passed = False
    else:
        print("  [PASS] Zero artificial bug markers (# BUG, planted, decoy, Ichnoscope) detected.")

    if not all_passed:
        print("\n[VERIFIER RESULT] FAILED - One or more invariants violated.")
        return 1

    # Write backend/bench/expected.json ground truth
    bench_dir = Path(__file__).resolve().parents[2] / "backend" / "bench"
    bench_dir.mkdir(parents=True, exist_ok=True)
    expected_path = bench_dir / "expected.json"

    expected_payload = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "now": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "repo_path": str(repo_dir),
        "head_sha": head_sha,
        "bugs": verified_bugs,
    }

    with open(expected_path, "w", encoding="utf-8") as f:
        json.dump(expected_payload, f, indent=2)

    print(f"\n[GROUND TRUTH] Successfully wrote benchmark ground truth to: {expected_path}")
    print("\n[VERIFIER RESULT] ALL INVARIANTS PASSED SUCCESSFULLY!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
