"""Database initialization, schema management, and unified SQLite / Turso libSQL client."""

import base64
from contextlib import contextmanager
import logging
import os
from pathlib import Path
import sqlite3
from typing import Any, Iterator

import httpx

logger = logging.getLogger(__name__)

DEFAULT_RUNS_DB: str = "ichnoscope_runs.db"


class TursoCursor:
    """Cursor-like wrapper over Turso HTTP pipeline query results."""

    def __init__(self, rows: list[tuple], rowcount: int = -1):
        self._rows = rows
        self._idx = 0
        self.rowcount = rowcount

    def fetchone(self) -> tuple | None:
        if self._idx < len(self._rows):
            r = self._rows[self._idx]
            self._idx += 1
            return r
        return None

    def fetchall(self) -> list[tuple]:
        rem = self._rows[self._idx :]
        self._idx = len(self._rows)
        return rem


class TursoConnection:
    """Lightweight, thread-safe HTTP pipeline connection to Turso / libSQL database."""

    def __init__(self, url: str, token: str):
        normalized = url
        if normalized.startswith("libsql://"):
            normalized = "https://" + normalized[len("libsql://") :]
        elif not normalized.startswith("http"):
            normalized = f"https://{normalized}"
        self.endpoint = normalized.rstrip("/") + "/v2/pipeline"
        self.token = token
        self._client = httpx.Client(timeout=15.0)

    def execute(self, sql: str, params: tuple | list = ()) -> TursoCursor:
        args = []
        for p in params:
            if p is None:
                args.append({"type": "null"})
            elif isinstance(p, bool):
                args.append({"type": "integer", "value": "1" if p else "0"})
            elif isinstance(p, int):
                args.append({"type": "integer", "value": str(p)})
            elif isinstance(p, float):
                args.append({"type": "float", "value": p})
            elif isinstance(p, bytes):
                args.append({"type": "blob", "base64": base64.b64encode(p).decode("ascii")})
            else:
                args.append({"type": "text", "value": str(p)})

        payload = {
            "requests": [
                {
                    "type": "execute",
                    "stmt": {
                        "sql": sql,
                        "args": args,
                    },
                },
                {"type": "close"},
            ]
        }
        res = self._client.post(
            self.endpoint,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        res.raise_for_status()
        data = res.json()
        results = data.get("results", [])
        if not results:
            return TursoCursor([])

        first = results[0]
        if first.get("type") == "error":
            err_msg = str(first.get("error", {}).get("message", "Unknown Turso Error"))
            if "UNIQUE" in err_msg or "PRIMARY KEY" in err_msg:
                raise sqlite3.IntegrityError(err_msg)
            raise RuntimeError(f"Turso Error: {err_msg}")

        resp = first.get("response", {})
        result = resp.get("result", {})
        raw_rows = result.get("rows", [])
        rows = []
        for r in raw_rows:
            parsed_cols = []
            for col in r:
                c_type = col.get("type")
                val = col.get("value")
                if c_type == "null" or val is None:
                    parsed_cols.append(None)
                elif c_type == "integer":
                    try:
                        parsed_cols.append(int(val))
                    except (ValueError, TypeError):
                        parsed_cols.append(val)
                elif c_type == "float":
                    try:
                        parsed_cols.append(float(val))
                    except (ValueError, TypeError):
                        parsed_cols.append(val)
                else:
                    parsed_cols.append(val)
            rows.append(tuple(parsed_cols))
        affected = result.get("affected_row_count", 0)
        return TursoCursor(rows, rowcount=affected)

    def commit(self) -> None:
        pass

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TursoConnection":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def get_db_path(custom_path: str | Path | None = None) -> Path:
    """Return database file path, creating parent directories if needed."""
    target = custom_path or DEFAULT_RUNS_DB
    path = Path(target)
    if not path.is_absolute() and target == "ichnoscope_runs.db":
        root_dir = Path(__file__).resolve().parents[2]
        path = root_dir / target
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def get_db(db_path: str | Path | None = None) -> Iterator[Any]:
    """Yield database connection: Turso if credentials exist, otherwise local SQLite."""
    turso_url = os.environ.get("TURSO_DATABASE_URL") or os.environ.get("TURSO_DB_URL") or os.environ.get("LIBSQL_URL")
    turso_token = os.environ.get("TURSO_AUTH_TOKEN") or os.environ.get("TURSO_TOKEN") or os.environ.get("LIBSQL_AUTH_TOKEN")
    if turso_url and turso_token and db_path is None and DEFAULT_RUNS_DB == "ichnoscope_runs.db":
        with TursoConnection(turso_url.strip(), turso_token.strip()) as conn:
            yield conn
    else:
        path = get_db_path(db_path)
        with sqlite3.connect(path) as conn:
            yield conn


def init_db(db_path: str | Path | None = None) -> Path | str:
    """Initialize database tables for runs, execution logs, and incident deduplication."""
    turso_url = os.environ.get("TURSO_DATABASE_URL") or os.environ.get("TURSO_DB_URL") or os.environ.get("LIBSQL_URL")
    turso_token = os.environ.get("TURSO_AUTH_TOKEN") or os.environ.get("TURSO_TOKEN") or os.environ.get("LIBSQL_AUTH_TOKEN")

    tables = [
        """
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            fingerprint TEXT NOT NULL,
            status TEXT NOT NULL,
            state_json TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS run_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            step TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp REAL NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS seen (
            fp              TEXT PRIMARY KEY,
            issue_number    INTEGER,
            count           INTEGER NOT NULL DEFAULT 1,
            first_seen      REAL NOT NULL,
            last_seen       REAL NOT NULL,
            last_comment_at REAL
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_runs_updated ON runs (updated_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_logs_run_id ON run_logs (run_id, timestamp);",
    ]

    if turso_url and turso_token and db_path is None and DEFAULT_RUNS_DB == "ichnoscope_runs.db":
        with TursoConnection(turso_url.strip(), turso_token.strip()) as conn:
            for stmt in tables:
                conn.execute(stmt)
        return turso_url

    path = get_db_path(db_path)
    with sqlite3.connect(path) as conn:
        for stmt in tables:
            conn.execute(stmt)
    return path
