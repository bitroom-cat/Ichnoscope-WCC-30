"""Administrative and dashboard REST API endpoints for incident run reviews."""

from typing import Any

from fastapi import APIRouter, HTTPException

from ichnoscope.config import get_settings
from ichnoscope.publisher import publish_issue
from ichnoscope.store import get_run, get_run_logs, list_runs, save_run

router = APIRouter(prefix="/api")


@router.get("/runs")
def api_list_runs() -> list[dict[str, Any]]:
    """List recent incident triage runs for the dashboard."""
    raw_runs = list_runs(limit=50)
    items: list[dict[str, Any]] = []

    for run_id, state in raw_runs:
        inc = state.incident
        expl = state.explanation
        cul = state.culprit

        items.append(
            {
                "id": run_id,
                "status": state.status,
                "severity": state.severity,
                "fingerprint": state.fingerprint,
                "is_regression": state.is_regression,
                "issue_url": state.issue_url,
                "incident": inc.model_dump(mode="json") if inc else None,
                "explanation": expl.model_dump(mode="json") if expl else None,
                "culprit": cul.model_dump(mode="json") if cul else None,
                "logs_count": len(state.logs),
            }
        )
    return items


@router.get("/runs/{run_id}")
def api_get_run(run_id: str) -> dict[str, Any]:
    """Retrieve detailed execution state and audit trail for a run."""
    state = get_run(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    inc = state.incident
    expl = state.explanation
    cul = state.culprit
    detailed_logs = get_run_logs(run_id)

    return {
        "id": run_id,
        "status": state.status,
        "severity": state.severity,
        "fingerprint": state.fingerprint,
        "is_regression": state.is_regression,
        "issue_url": state.issue_url,
        "incident": inc.model_dump(mode="json") if inc else None,
        "explanation": expl.model_dump(mode="json") if expl else None,
        "culprit": cul.model_dump(mode="json") if cul else None,
        "logs": detailed_logs if detailed_logs else state.logs,
    }


@router.post("/runs/{run_id}/approve")
def api_approve_run(run_id: str) -> dict[str, Any]:
    """Approve a draft issue and publish it to GitHub."""
    state = get_run(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    if state.status == "published":
        return {"status": "already_published", "issue_url": state.issue_url}

    if not state.incident:
        raise HTTPException(status_code=400, detail="Cannot approve run without parsed incident")

    settings = get_settings()
    try:
        pub_res = publish_issue(
            incident=state.incident,
            culprit=state.culprit,
            explanation=state.explanation,
            severity=state.severity or "P3-Medium",
            fingerprint=state.fingerprint,
            is_regression=state.is_regression,
            settings=settings,
        )
        state.status = "published"
        state.issue_url = pub_res.issue_url
        state.logs.append(f"[INFO] admin: Approved draft; published issue #{pub_res.issue_number}")
        save_run(run_id, state)

        return {
            "status": "published",
            "issue_number": pub_res.issue_number,
            "issue_url": pub_res.issue_url,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Publishing failed: {exc}") from exc


@router.post("/runs/{run_id}/reject")
def api_reject_run(run_id: str) -> dict[str, Any]:
    """Reject a draft issue without publishing to GitHub."""
    state = get_run(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    state.status = "rejected"
    state.logs.append("[INFO] admin: Rejected draft; issue will not be created")
    save_run(run_id, state)
    return {"status": "rejected"}


@router.get("/settings")
def api_get_settings() -> dict[str, Any]:
    """Return sanitized system settings."""
    settings = get_settings()
    return settings.safe_summary()


@router.get("/health")
def api_get_health() -> list[dict[str, Any]]:
    """Return component health overview for the dashboard."""
    settings = get_settings()
    return [
        {
            "key": "sentry",
            "name": "Sentry Webhook Listener",
            "status": "healthy" if settings.sentry_client_secret else "degraded",
            "description": "Ingesting error events from Sentry",
            "latency_ms": 15,
        },
        {
            "key": "github",
            "name": "GitHub Integration",
            "status": "healthy" if settings.github_token else "degraded",
            "description": "Blame lookup and issue publishing",
            "latency_ms": 45,
        },
        {
            "key": "llm",
            "name": "LLM Inference Pipeline",
            "status": "healthy" if (settings.use_stub_llm or settings.llm_providers()) else "degraded",
            "description": "Root-cause explanation generation",
            "latency_ms": 110,
        },
        {
            "key": "slack",
            "name": "Slack Notifications",
            "status": "healthy" if settings.slack_webhook_url else "degraded",
            "description": "Incoming webhook alert dispatcher",
            "latency_ms": 20,
        },
    ]
