"""End-to-end incident triage pipeline coordinating parsing, deduplication, blame, explanation, and dispatch."""

import logging
import uuid

import httpx

from ichnoscope.blame import find_culprit
from ichnoscope.config import Settings
from ichnoscope.dedupe import (
    attach,
    bump,
    claim,
    lookup,
)
from ichnoscope.dedupe import (
    fingerprint as calc_fingerprint,
)
from ichnoscope.explain import explain_with_details
from ichnoscope.models import RunState
from ichnoscope.notify import notify_slack
from ichnoscope.parse import parse_sentry
from ichnoscope.publisher import publish_issue, publish_repeat_comment
from ichnoscope.severity import rate_with_reason
from ichnoscope.store import record_log, save_run

logger = logging.getLogger(__name__)


def run_pipeline(
    payload: dict,
    *,
    run_id: str | None = None,
    auto_publish: bool = True,
    db_path: str | None = None,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
) -> RunState:
    """Execute the complete incident investigation and triage pipeline."""
    if settings is None:
        from ichnoscope.config import get_settings

        settings = get_settings()

    active_run_id = run_id or uuid.uuid4().hex[:10]
    state = RunState(payload=payload, status="received")

    def _log(step: str, message: str, level: str = "INFO") -> None:
        entry = f"[{level}] {step}: {message}"
        state.logs.append(entry)
        record_log(active_run_id, step, message, level=level, db_path=db_path)

    _log("gateway", f"Received incident payload for run {active_run_id}")
    save_run(active_run_id, state, db_path=db_path)

    http_client = client or httpx.Client()
    close_client = client is None

    try:
        # Step 1: Parse Sentry payload
        state.status = "parsing"
        try:
            incident = parse_sentry(payload, path_prefix_strip=settings.path_prefix_strip)
            state.incident = incident
            _log("parse", f"Parsed incident: {incident.exception_type} at {incident.file_path}:{incident.line_number}")
        except Exception as exc:  # noqa: BLE001
            state.status = "failed"
            _log("parse", f"Failed to parse payload: {exc}", level="ERROR")
            save_run(active_run_id, state)
            return state

        # Step 2: Deduplicate & Fingerprint
        fp = calc_fingerprint(incident)
        state.fingerprint = fp
        is_new = claim(fp, db_path=db_path)

        if not is_new:
            # Repeat event handling
            prev_row = lookup(fp, db_path=db_path)
            bump_count, comment_due = bump(fp, db_path=db_path)
            _log("dedupe", f"Fingerprint {fp} previously seen. Count incremented to {bump_count}")

            if prev_row and prev_row.issue_number and comment_due:
                _log("dedupe", f"Posting repeat comment to issue #{prev_row.issue_number}")
                publish_repeat_comment(
                    issue_number=prev_row.issue_number,
                    count=bump_count,
                    settings=settings,
                    client=http_client,
                )

            state.status = "suppressed"
            save_run(active_run_id, state, db_path=db_path)
            return state

        _log("dedupe", f"Claimed new incident fingerprint: {fp}")

        # Step 3: Blame & Git History
        state.status = "blaming"
        blame_res = find_culprit(incident, settings=settings, client=http_client)
        state.culprit = blame_res.culprit

        if blame_res.culprit:
            _log(
                "blame",
                f"Suspect identified via {blame_res.source}: {blame_res.culprit.sha[:7]} "
                f"by @{blame_res.culprit.author_login or 'unknown'} (confidence: {blame_res.culprit.confidence})",
            )
        else:
            _log("blame", f"No suspect identified: {blame_res.error or 'blame inconclusive'}", level="WARN")

        # Step 4: Explain with LLM
        state.status = "explaining"
        explain_res = explain_with_details(
            incident,
            state.culprit,
            other_commits=blame_res.other_commits,
            settings=settings,
            client=http_client,
        )
        state.explanation = explain_res.explanation

        if explain_res.explanation:
            _log(
                "explain",
                f"Root cause hypothesis generated via {explain_res.source} "
                f"(provider: {explain_res.provider or 'internal'})",
            )
        else:
            _log(
                "explain",
                f"LLM explanation unavailable: {explain_res.reason}. Falling back to evidence-only template.",
                level="WARN",
            )

        # Step 5: Severity Rating
        severity, severity_reason = rate_with_reason(incident, settings=settings)
        state.severity = severity
        _log("severity", f"Rated severity: {severity} ({severity_reason})")

        # Step 6: Dispatch / Publish Issue
        if auto_publish:
            try:
                pub_res = publish_issue(
                    incident=incident,
                    culprit=state.culprit,
                    explanation=state.explanation,
                    severity=severity,
                    severity_reason=severity_reason,
                    fingerprint=fp,
                    is_regression=state.is_regression,
                    settings=settings,
                    client=http_client,
                )
                state.issue_url = pub_res.issue_url
                state.status = "published"
                attach(fp, pub_res.issue_number, db_path=db_path)
                _log("dispatch", f"Published GitHub issue #{pub_res.issue_number}: {pub_res.issue_url}")

                # Optional Slack notification
                notify_slack(
                    title=f"{incident.exception_type}: {incident.error_message}",
                    severity=severity,
                    assignee=pub_res.assignee,
                    issue_url=pub_res.issue_url,
                    settings=settings,
                    client=http_client,
                )
            except Exception as exc:  # noqa: BLE001
                state.status = "failed"
                _log("dispatch", f"Failed to publish issue: {exc}", level="ERROR")
        else:
            state.status = "draft_ready"
            _log("dispatch", "Issue draft prepared and awaiting human approval")

        save_run(active_run_id, state, db_path=db_path)
        return state

    except Exception as exc:  # noqa: BLE001
        state.status = "failed"
        _log("pipeline", f"Unexpected pipeline failure: {exc}", level="ERROR")
        save_run(active_run_id, state, db_path=db_path)
        return state
    finally:
        if close_client:
            http_client.close()
