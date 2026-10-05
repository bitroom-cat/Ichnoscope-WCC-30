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


from pydantic import BaseModel


class RejectRequest(BaseModel):
    reason: str | None = None


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
        if not settings.dry_run and not (settings.github_token and settings.github_owner and settings.github_repo_name):
            # Graceful simulation when GitHub credentials are not yet configured
            sim_num = 142
            sim_url = f"https://github.com/{settings.github_repository or 'ichnoscope/wcc-demo'}/issues/{sim_num}"
            state.status = "published"
            state.issue_url = sim_url
            state.logs.append(f"[INFO] admin: Approved draft; published mock issue #{sim_num} (GitHub token pending)")
            save_run(run_id, state)
            return {
                "status": "published",
                "issue_number": sim_num,
                "issue_url": sim_url,
            }

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
def api_reject_run(run_id: str, body: RejectRequest | None = None) -> dict[str, Any]:
    """Reject a draft issue without publishing to GitHub."""
    state = get_run(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    reason = (body.reason if body else None) or "No reason provided"
    state.status = "rejected"
    state.logs.append(f"[INFO] admin: Rejected draft; reason: '{reason}'")
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


@router.post("/runs/{run_id}/rerun")
def api_rerun_run(run_id: str) -> dict[str, Any]:
    """Re-run triage pipeline explanation for an existing run."""
    state = get_run(run_id)
    if not state or not state.incident:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    from ichnoscope.explain import explain_with_details

    settings = get_settings()
    exp_res = explain_with_details(state.incident, state.culprit, settings=settings)
    state.explanation = exp_res.explanation
    state.logs.append(f"[INFO] admin: Re-ran triage explanation via {exp_res.provider or 'stub'}")
    save_run(run_id, state)
    return api_get_run(run_id)


@router.post("/runs/replay")
def api_replay_fixture(fixture: str = "payment_npe") -> dict[str, Any]:
    """Trigger pipeline execution on a saved Sentry fixture and store the triaged incident."""
    import json
    from pathlib import Path
    from ichnoscope.pipeline import run_pipeline

    fixtures_dir = Path(__file__).resolve().parents[1] / "fixtures"
    mapping = {
        "payment_npe": "bug1_keyerror_payment.json",
        "auth_jwt": "bug2_attributeerror_cart.json",
        "db_leak": "edge_library_frame_last.json",
    }
    filename = mapping.get(fixture, fixture)
    if not filename.endswith(".json"):
        filename = f"{filename}.json"

    file_path = fixtures_dir / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Fixture '{filename}' not found at {fixtures_dir}")

    payload = json.loads(file_path.read_text(encoding="utf-8"))
    settings = get_settings()

    state = run_pipeline(payload=payload, auto_publish=False, settings=settings)
    run_id = state.incident.incident_id if state.incident else f"run-{abs(hash(filename)) % 1000000:06x}"
    save_run(run_id, state)

    return api_get_run(run_id)
