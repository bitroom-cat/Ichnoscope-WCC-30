"""Database initialization and schema management for incident runs and audit logs."""

import sqlite3
from pathlib import Path

DEFAULT_RUNS_DB: str = "ichnoscope_runs.db"


def get_db_path(custom_path: str | Path | None = None) -> Path:
    """Return database file path, creating parent directories if needed."""
    path = Path(custom_path or DEFAULT_RUNS_DB)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def init_db(db_path: str | Path | None = None) -> Path:
    """Initialize database tables for runs and execution logs."""
    path = get_db_path(db_path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                fingerprint TEXT NOT NULL,
                status TEXT NOT NULL,
                state_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                step TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp REAL NOT NULL,
                FOREIGN KEY (run_id) REFERENCES runs (id)
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_updated ON runs (updated_at DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_run_id ON run_logs (run_id, timestamp);")
    return path
