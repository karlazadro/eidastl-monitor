import sqlite3
import pandas as pd
from .util import utc_now_iso

def run_dq_checks(conn: sqlite3.Connection, run_id: int) -> None:
    df = pd.read_sql_query(
        "SELECT * FROM tsp_services WHERE run_id = ?",
        conn,
        params=(run_id,)
    )

    results = []

    def add(rule_id, desc, severity, failed_keys):
        results.append({
            "run_id": run_id,
            "rule_id": rule_id,
            "rule_description": desc,
            "severity": severity,
            "failed_count": len(failed_keys),
            "sample_keys": ",".join(failed_keys[:10]),
            "created_at": utc_now_iso()
        })

    missing_type = df[df["service_type_identifier"].isna() | (df["service_type_identifier"] == "")]
    add("R1", "ServiceTypeIdentifier must not be empty", "error", missing_type["service_key"].tolist())

    missing_provider = df[df["provider_key"].isna() | (df["provider_key"] == "")]
    add("R2", "provider_key must not be empty", "error", missing_provider["service_key"].tolist())

    missing_status = df[df["current_status"].isna() | (df["current_status"] == "")]
    add("R3", "ServiceStatus should not be empty", "warn", missing_status["service_key"].tolist())

    for r in results:
        conn.execute(
            """INSERT OR REPLACE INTO dq_results
               (run_id, rule_id, rule_description, severity, failed_count, sample_keys, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (r["run_id"], r["rule_id"], r["rule_description"], r["severity"], r["failed_count"], r["sample_keys"], r["created_at"])
        )
    conn.commit()
