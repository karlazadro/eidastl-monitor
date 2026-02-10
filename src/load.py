import sqlite3
import pandas as pd
from .util import utc_now_iso

def start_run(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    cur.execute("INSERT INTO runs (started_at, status) VALUES (?, ?)", (utc_now_iso(), "ok"))
    conn.commit()
    return int(cur.lastrowid)

def finish_run(conn: sqlite3.Connection, run_id: int, status: str, notes: str | None = None) -> None:
    conn.execute(
        "UPDATE runs SET finished_at = ?, status = ?, notes = ? WHERE run_id = ?",
        (utc_now_iso(), status, notes, run_id)
    )
    conn.commit()

def insert_source(conn, run_id: int, source_type: str, url: str, fetched_at: str, sha256: str, bytes_: int, country_code: str | None = None):
    conn.execute(
        "INSERT INTO sources (run_id, source_type, country_code, url, fetched_at, sha256, bytes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (run_id, source_type, country_code, url, fetched_at, sha256, bytes_)
    )
    conn.commit()

def load_snapshot(conn, run_id: int, providers_df: pd.DataFrame, services_df: pd.DataFrame) -> None:
    providers_df = providers_df.copy()
    services_df = services_df.copy()
    providers_df["run_id"] = run_id
    services_df["run_id"] = run_id

    providers_df.to_sql("tsp_providers", conn, if_exists="append", index=False)
    services_df.to_sql("tsp_services", conn, if_exists="append", index=False)
