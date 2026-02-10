from __future__ import annotations

from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "eidastl.sqlite"
OUTDIR = ROOT / "dashboard_screenshots" / "auto"

STATUS_MAP = {
    "HTTP://URI.ETSI.ORG/TRSTSVC/TRUSTEDLIST/SVCSTATUS/DEPRECATEDATNATIONALLEVEL": "DEPRECATED_NL",
    "HTTP://URI.ETSI.ORG/TRSTSVC/TRUSTEDLIST/SVCSTATUS/GRANTED": "GRANTED",
    "HTTP://URI.ETSI.ORG/TRSTSVC/TRUSTEDLIST/SVCSTATUS/RECOGNISEDATNATIONALLEVEL": "RECOGNISED_NL",
    "HTTP://URI.ETSI.ORG/TRSTSVC/TRUSTEDLIST/SVCSTATUS/WITHDRAWN": "WITHDRAWN",
}
STATUS_ORDER = ["GRANTED", "RECOGNISED_NL", "DEPRECATED_NL", "WITHDRAWN"]

def _save_bar(series: pd.Series, title: str, xlabel: str, ylabel: str, filename: str, rotate=0):
    ax = series.plot(kind="bar", figsize=(10, 4))
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=rotate, ha="right" if rotate else "center")
    plt.tight_layout()
    plt.savefig(OUTDIR / filename, dpi=200)
    plt.close()

def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError("Nema eidastl.sqlite. Pokreni: python -m src.run_all")

    OUTDIR.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(DB_PATH)
    try:
        run_id = int(pd.read_sql_query("SELECT run_id FROM v_latest_run", con).iloc[0, 0])

        # --- SNAPSHOT (services) ---
        df = pd.read_sql_query(
            "SELECT country_code, current_status, service_key FROM v_latest_services",
            con
        )
        df["country_code"] = df["country_code"].astype(str).str.strip()
        df["current_status"] = df["current_status"].astype(str).str.strip().str.upper()
        df["status_label"] = df["current_status"].map(STATUS_MAP).fillna(df["current_status"])

        g = (
            df.groupby(["country_code", "status_label"])["service_key"]
            .nunique()
            .rename("count")
            .reset_index()
        )
        pivot = (
            g.pivot_table(index="country_code", columns="status_label", values="count", fill_value=0, aggfunc="sum")
            .sort_index()
        )
        cols = [c for c in STATUS_ORDER if c in pivot.columns] + [c for c in pivot.columns if c not in STATUS_ORDER]
        pivot = pivot[cols]

        pivot.to_csv(OUTDIR / "status_counts_by_country.csv", index=True)

        # percent stacked (najbitniji)
        pct = pivot.div(pivot.sum(axis=1).replace({0: np.nan}), axis=0) * 100
        ax = pct.plot(kind="bar", stacked=True, figsize=(14, 6))
        ax.set_title(f"Service status distribution by country (percent, run_id={run_id})")
        ax.set_xlabel("Country")
        ax.set_ylabel("Percent")
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(OUTDIR / "status_distribution_stacked_percent.png", dpi=200)
        plt.close()

        # total services
        totals = pivot.sum(axis=1).sort_values(ascending=False)
        _save_bar(
            totals,
            title=f"Total distinct services by country (run_id={run_id})",
            xlabel="Country",
            ylabel="Distinct services",
            filename="total_services_by_country.png",
            rotate=0
        )

        # KPI: GRANTED / total
        if "GRANTED" in pivot.columns:
            kpi_granted = (pivot["GRANTED"] / pivot.sum(axis=1).replace({0: np.nan}) * 100).sort_values(ascending=False)
            _save_bar(
                kpi_granted,
                title=f"KPI: Active % by country (GRANTED/total, run_id={run_id})",
                xlabel="Country",
                ylabel="Active %",
                filename="kpi_active_pct_granted.png",
                rotate=0
            )
            kpi_granted.rename("active_pct_granted").to_csv(OUTDIR / "kpi_active_pct_granted.csv", index=True)

        # KPI: (GRANTED+RECOGNISED)/total
        if "GRANTED" in pivot.columns and "RECOGNISED_NL" in pivot.columns:
            kpi_plus = ((pivot["GRANTED"] + pivot["RECOGNISED_NL"]) / pivot.sum(axis=1).replace({0: np.nan}) * 100).sort_values(ascending=False)
            _save_bar(
                kpi_plus,
                title=f"KPI: Active % by country ((GRANTED+RECOGNISED)/total, run_id={run_id})",
                xlabel="Country",
                ylabel="Active %",
                filename="kpi_active_pct_granted_plus_recognised.png",
                rotate=0
            )
            kpi_plus.rename("active_pct_granted_plus_recognised").to_csv(
                OUTDIR / "kpi_active_pct_granted_plus_recognised.csv", index=True
            )

        # --- CHANGES (monitoring) ---
        ch = pd.read_sql_query(
            """
            SELECT change_type, country_code
            FROM change_log
            WHERE run_id = ?
            """,
            con,
            params=(run_id,),
        )

        if not ch.empty:
            by_type = ch.groupby("change_type").size().sort_values(ascending=False)
            _save_bar(
                by_type,
                title=f"Changes by type (run_id={run_id})",
                xlabel="Change type",
                ylabel="Count",
                filename="changes_by_type.png",
                rotate=30
            )
            by_country = ch.groupby("country_code").size().sort_values(ascending=False)
            _save_bar(
                by_country,
                title=f"Changes by country (run_id={run_id})",
                xlabel="Country",
                ylabel="Count",
                filename="changes_by_country.png",
                rotate=0
            )

        print("OK")
        print(f"run_id={run_id}")
        print(f"outdir={OUTDIR}")
    finally:
        con.close()

if __name__ == "__main__":
    main()
