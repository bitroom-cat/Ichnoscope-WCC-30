"""Unit tests for backend/ichnoscope/store.py and backend/ichnoscope/db.py."""

from pathlib import Path

from ichnoscope.models import RunState
from ichnoscope.store import (
    get_run,
    get_run_logs,
    list_runs,
    record_log,
    save_run,
)


def test_save_and_get_run(tmp_path: Path):
    db_file = tmp_path / "runs.db"
    run_id = "run-test-1"
    initial_state = RunState(
        payload={"event_id": "evt-123"},
        fingerprint="fp1234567890",
        status="received",
        logs=["Received webhook payload"],
    )

    save_run(run_id, initial_state, db_path=db_file)

    loaded = get_run(run_id, db_path=db_file)
    assert loaded is not None
    assert loaded.status == "received"
    assert loaded.fingerprint == "fp1234567890"
    assert loaded.payload == {"event_id": "evt-123"}
    assert loaded.logs == ["Received webhook payload"]


def test_update_run_status(tmp_path: Path):
    db_file = tmp_path / "runs.db"
    run_id = "run-test-2"
    state = RunState(payload={}, status="parsing")
    save_run(run_id, state, db_path=db_file)

    state.status = "draft_ready"
    state.issue_url = "https://github.com/owner/repo/issues/10"
    save_run(run_id, state, db_path=db_file)

    updated = get_run(run_id, db_path=db_file)
    assert updated is not None
    assert updated.status == "draft_ready"
    assert updated.issue_url == "https://github.com/owner/repo/issues/10"


def test_list_runs(tmp_path: Path):
    db_file = tmp_path / "runs.db"
    save_run("run-1", RunState(payload={}, status="received"), db_path=db_file, now=100.0)
    save_run("run-2", RunState(payload={}, status="draft_ready"), db_path=db_file, now=200.0)

    runs = list_runs(db_path=db_file)
    assert len(runs) == 2
    assert runs[0][0] == "run-2"
    assert runs[1][0] == "run-1"


def test_run_logs(tmp_path: Path):
    db_file = tmp_path / "runs.db"
    run_id = "run-log-test"

    record_log(run_id, "parse", "Parsed 3 stack frames", level="INFO", db_path=db_file, now=10.0)
    record_log(run_id, "blame", "Suspect commit identified", level="INFO", db_path=db_file, now=12.0)

    logs = get_run_logs(run_id, db_path=db_file)
    assert len(logs) == 2
    assert logs[0]["step"] == "parse"
    assert logs[0]["message"] == "Parsed 3 stack frames"
    assert logs[1]["step"] == "blame"
