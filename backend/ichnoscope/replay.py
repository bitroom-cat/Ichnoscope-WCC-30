"""CLI utility replaying saved Sentry JSON payloads through the triage pipeline for demos and offline evaluation."""

import argparse
import json
import sys
from pathlib import Path

from ichnoscope.config import get_settings, load_settings
from ichnoscope.pipeline import run_pipeline


def replay_fixture(
    fixture_path: Path | str,
    *,
    dry_run: bool = True,
    auto_publish: bool = True,
    db_path: str | None = None,
) -> int:
    """Replay a Sentry JSON payload through the pipeline and print formatted results."""
    path = Path(fixture_path)
    if not path.is_file():
        print(f"Error: Fixture file not found: {path}", file=sys.stderr)
        return 1

    try:
        raw_text = path.read_text(encoding="utf-8")
        payload = json.loads(raw_text)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: Failed to read JSON fixture from {path}: {exc}", file=sys.stderr)
        return 1

    current = get_settings()
    # Override dry_run if explicitly requested
    settings = load_settings({
        **current.safe_summary(),
        "DRY_RUN": "true" if dry_run else "false",
    })

    print(f"=== Replaying Incident: {path.name} ===")
    state = run_pipeline(
        payload=payload,
        auto_publish=auto_publish,
        db_path=db_path,
        settings=settings,
    )

    print(f"Status: {state.status.upper()}")
    if state.incident:
        inc = state.incident
        print(f"Incident: {inc.exception_type} at {inc.file_path}:{inc.line_number}")
        print(f"Occurrence: {inc.occurred_at.isoformat()} | Env: {inc.environment}")
        print(f"Impact: {inc.users_affected} users, {inc.event_count} events")

    if state.culprit:
        cul = state.culprit
        print(f"Suspect: {cul.sha[:7]} by @{cul.author_login or 'unknown'} (confidence: {cul.confidence})")
        print(f"Commit msg: {cul.message.splitlines()[0] if cul.message else ''}")

    if state.explanation:
        exp = state.explanation
        print(f"Domain: {exp.domain}")
        print(f"Hypothesis: {exp.root_cause_hypothesis}")
        print("Checklist:")
        for idx, item in enumerate(exp.checklist, 1):
            print(f"  {idx}. {item}")

    if state.severity:
        print(f"Severity: {state.severity}")

    if state.issue_url:
        print(f"Issue: {state.issue_url}")

    print("\n--- Pipeline Logs ---")
    for log in state.logs:
        print(log)

    return 0 if state.status in ("published", "draft_ready", "suppressed") else 1


def main() -> None:
    """CLI entrypoint for replaying Sentry payloads."""
    parser = argparse.ArgumentParser(
        description="Replay Sentry incident payloads through Ichnoscope triage pipeline."
    )
    parser.add_argument("fixture", type=str, help="Path to Sentry JSON fixture file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Simulate issue creation without posting to GitHub (default: True)",
    )
    parser.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="Post real issue to GitHub",
    )
    parser.add_argument(
        "--draft-only",
        dest="auto_publish",
        action="store_false",
        default=True,
        help="Stop at draft_ready without publishing",
    )

    args = parser.parse_args()
    code = replay_fixture(args.fixture, dry_run=args.dry_run, auto_publish=args.auto_publish)
    sys.exit(code)


if __name__ == "__main__":
    main()
