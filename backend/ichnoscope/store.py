"""Persistence layer storing incident RunState records and pipeline execution logs."""

import json
import sqlite3
import time
from pathlib import Path

from ichnoscope.db import init_db
from ichnoscope.models import RunState


def save_run(
    run_id: str,
    state: RunState,
    db_path: Path | str | None = None,
    now: float | None = None,
) -> None:
    """Insert or update a RunState record in the database."""
    path = init_db(db_path)
    ts = now if now is not None else time.time()
    state_json = json.dumps(state.model_dump(mode="json"))

    with sqlite3.connect(path) as conn:
        cursor = conn.execute("SELECT created_at FROM runs WHERE id = ?;", (run_id,))
        row = cursor.fetchone()
        if row:
            conn.execute(
                """
                UPDATE runs
                SET fingerprint = ?, status = ?, state_json = ?, updated_at = ?
                WHERE id = ?;
                """,
                (state.fingerprint, state.status, state_json, ts, run_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO runs (id, fingerprint, status, state_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (run_id, state.fingerprint, state.status, state_json, ts, ts),
            )


def get_run(run_id: str, db_path: Path | str | None = None) -> RunState | None:
    """Retrieve RunState by run ID, restoring logs from log store."""
    path = init_db(db_path)
    with sqlite3.connect(path) as conn:
        cursor = conn.execute("SELECT state_json FROM runs WHERE id = ?;", (run_id,))
        row = cursor.fetchone()
        if not row:
            return None
        data = json.loads(row[0])
        state = RunState.model_validate(data)

        # Merge stored log entries if not already embedded
        log_rows = conn.execute(
            "SELECT step, level, message FROM run_logs WHERE run_id = ? ORDER BY id ASC;",
            (run_id,),
        ).fetchall()
        if log_rows and not state.logs:
            rebuilt_logs = [f"[{r[1]}] {r[0]}: {r[2]}" for r in log_rows]
            state.logs = rebuilt_logs

        return state


def list_runs(
    db_path: Path | str | None = None,
    limit: int = 50,
) -> list[tuple[str, RunState]]:
    """List most recently updated runs up to limit."""
    path = init_db(db_path)
    with sqlite3.connect(path) as conn:
        cursor = conn.execute(
            """
            SELECT id, state_json FROM runs
            ORDER BY updated_at DESC
            LIMIT ?;
            """,
            (limit,),
        )
        results: list[tuple[str, RunState]] = []
        for r_id, raw_json in cursor.fetchall():
            try:
                state = RunState.model_validate(json.loads(raw_json))
                results.append((r_id, state))
            except Exception:  # noqa: BLE001, S112
                continue
        return results


def record_log(
    run_id: str,
    step: str,
    message: str,
    level: str = "INFO",
    db_path: Path | str | None = None,
    now: float | None = None,
) -> None:
    """Record an individual diagnostic log entry for a run."""
    path = init_db(db_path)
    ts = now if now is not None else time.time()
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO run_logs (run_id, step, level, message, timestamp)
            VALUES (?, ?, ?, ?, ?);
            """,
            (run_id, step, level, message, ts),
        )


def get_run_logs(
    run_id: str,
    db_path: Path | str | None = None,
) -> list[dict]:
    """Retrieve detailed log entries for a run in chronological order."""
    path = init_db(db_path)
    with sqlite3.connect(path) as conn:
        cursor = conn.execute(
            """
            SELECT step, level, message, timestamp FROM run_logs
            WHERE run_id = ?
            ORDER BY id ASC;
            """,
            (run_id,),
        )
        return [
            {
                "step": row[0],
                "level": row[1],
                "message": row[2],
                "timestamp": row[3],
            }
            for row in cursor.fetchall()
        ]
