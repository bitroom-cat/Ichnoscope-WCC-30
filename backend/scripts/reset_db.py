"""Utility script to empty/reset Turso libSQL and local SQLite tables for clean test runs."""

import os
import sqlite3
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from backend/.env or root .env
backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / ".env")
load_dotenv(backend_dir.parent / ".env")

sys.path.insert(0, str(backend_dir))
from ichnoscope.db import TursoConnection

def reset_turso():
    url = os.environ.get("TURSO_DATABASE_URL") or os.environ.get("TURSO_DB_URL") or os.environ.get("LIBSQL_URL")
    token = os.environ.get("TURSO_AUTH_TOKEN") or os.environ.get("TURSO_TOKEN") or os.environ.get("LIBSQL_AUTH_TOKEN")

    if not url or not token:
        print("[!] No Turso credentials found in environment. Skipping Turso reset.")
        return

    print(f"[*] Resetting Turso database: {url}")
    with TursoConnection(url, token) as conn:
        for table in ["run_logs", "runs", "seen"]:
            try:
                cnt_before = conn.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
                conn.execute(f"DELETE FROM {table};")
                cnt_after = conn.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
                print(f"    - Turso '{table}': {cnt_before} rows -> {cnt_after} rows")
            except Exception as e:
                print(f"    - Turso '{table}' error: {e}")

def reset_local_dbs():
    root_dir = backend_dir.parent
    local_dbs = [
        root_dir / "ichnoscope_runs.db",
        root_dir / "ichnoscope.db",
        backend_dir / "ichnoscope_runs.db",
        backend_dir / "ichnoscope.db",
    ]

    print("\n[*] Resetting local SQLite databases:")
    for path in local_dbs:
        if not path.exists():
            continue
        try:
            with sqlite3.connect(path) as conn:
                cur = conn.cursor()
                tables = [
                    row[0]
                    for row in cur.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
                    ).fetchall()
                ]
                for t in tables:
                    b = cur.execute(f"SELECT COUNT(*) FROM {t};").fetchone()[0]
                    cur.execute(f"DELETE FROM {t};")
                    a = cur.execute(f"SELECT COUNT(*) FROM {t};").fetchone()[0]
                    print(f"    - {path.name} '{t}': {b} rows -> {a} rows")
                conn.commit()
        except Exception as e:
            print(f"    - {path.name} error: {e}")

if __name__ == "__main__":
    reset_turso()
    reset_local_dbs()
    print("\n[+] Reset complete! Databases are clean and ready for fresh logs.")
