import sqlite3
import pandas as pd
from .util import utc_now_iso

def get_last_two_runs(conn: sqlite3.Connection):
    rows = conn.execute(
        "SELECT run_id FROM runs WHERE status='ok' ORDER BY run_id DESC LIMIT 2"
    ).fetchall()
    if len(rows) < 2:
        return None
    newest, prev = int(rows[0][0]), int(rows[1][0])
    return prev, newest

def detect_changes(conn: sqlite3.Connection) -> None:
    pair = get_last_two_runs(conn)
    if not pair:
        return
    prev_run, new_run = pair

    prev = pd.read_sql_query("SELECT * FROM tsp_services WHERE run_id=?", conn, params=(prev_run,))
    new = pd.read_sql_query("SELECT * FROM tsp_services WHERE run_id=?", conn, params=(new_run,))

    prev_idx = prev.set_index("service_key")
    new_idx = new.set_index("service_key")

    added_keys = list(set(new_idx.index) - set(prev_idx.index))
    for k in added_keys:
        row = new_idx.loc[k]
        _insert(conn, new_run, "service_added", k, row["country_code"], None, row["current_status"])

    removed_keys = list(set(prev_idx.index) - set(new_idx.index))
    for k in removed_keys:
        row = prev_idx.loc[k]
        _insert(conn, new_run, "service_removed", k, row["country_code"], row["current_status"], None)

    common = list(set(prev_idx.index) & set(new_idx.index))
    for k in common:
        old = prev_idx.loc[k]["current_status"]
        newv = new_idx.loc[k]["current_status"]
        if (old or "") != (newv or ""):
            cc = new_idx.loc[k]["country_code"]
            _insert(conn, new_run, "status_changed", k, cc, old, newv)

    conn.commit()

def _insert(conn, run_id, change_type, entity_key, country_code, old_value, new_value):
    conn.execute(
        """INSERT OR REPLACE INTO change_log
           (run_id, change_type, entity_key, country_code, old_value, new_value, detected_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (run_id, change_type, entity_key, country_code, old_value, new_value, utc_now_iso())
    )
