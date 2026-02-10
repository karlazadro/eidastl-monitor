from .config import Config
from .db import connect, apply_schema
from .extract import download, safe_filename
from .transform import parse_lotl_for_pointers, parse_trusted_list
from .load import start_run, finish_run, insert_source, load_snapshot
from .dq_checks import run_dq_checks
from .detect_changes import detect_changes

def main():
    cfg = Config.from_env()
    conn = connect(cfg.db_path)
    apply_schema(conn, cfg.schema_path)

    run_id = start_run(conn)

    try:
        lotl_file = cfg.raw_dir / safe_filename("lotl")
        lotl_meta = download(cfg.lotl_url, lotl_file)
        insert_source(conn, run_id, "lotl", lotl_meta["url"], lotl_meta["fetched_at"], lotl_meta["sha256"], lotl_meta["bytes"])

        pointers = parse_lotl_for_pointers(str(lotl_file))
        pointers = [p for p in pointers if p.country_code in cfg.countries]

        all_providers = []
        all_services = []

        for p in pointers:
            tl_file = cfg.raw_dir / safe_filename("tl", p.country_code)
            tl_meta = download(p.tl_url, tl_file)
            insert_source(conn, run_id, "tl", tl_meta["url"], tl_meta["fetched_at"], tl_meta["sha256"], tl_meta["bytes"], country_code=p.country_code)

            providers_df, services_df = parse_trusted_list(str(tl_file), p.country_code)
            all_providers.append(providers_df)
            all_services.append(services_df)

        if all_providers:
            import pandas as pd
            providers = pd.concat(all_providers, ignore_index=True).drop_duplicates(subset=["provider_key"])
            services = pd.concat(all_services, ignore_index=True).drop_duplicates(subset=["service_key"])
            load_snapshot(conn, run_id, providers, services)

        run_dq_checks(conn, run_id)
        detect_changes(conn)

        finish_run(conn, run_id, "ok", notes=f"Countries: {cfg.countries}")
        print(f"Run OK: {run_id}")

    except Exception as e:
        finish_run(conn, run_id, "failed", notes=str(e))
        raise

if __name__ == "__main__":
    main()
