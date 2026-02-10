PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
  run_id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS sources (
  source_id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  source_type TEXT NOT NULL,
  country_code TEXT,
  url TEXT NOT NULL,
  fetched_at TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  bytes INTEGER NOT NULL,
  record_hint INTEGER,
  FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS tsp_providers (
  run_id INTEGER NOT NULL,
  provider_key TEXT NOT NULL,
  country_code TEXT NOT NULL,
  tsp_name TEXT NOT NULL,
  tsp_uri TEXT,
  PRIMARY KEY (run_id, provider_key),
  FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS tsp_services (
  run_id INTEGER NOT NULL,
  service_key TEXT NOT NULL,
  provider_key TEXT NOT NULL,
  country_code TEXT NOT NULL,
  service_type_identifier TEXT NOT NULL,
  service_name TEXT,
  current_status TEXT,
  status_starting_time TEXT,
  PRIMARY KEY (run_id, service_key),
  FOREIGN KEY (run_id, provider_key) REFERENCES tsp_providers(run_id, provider_key)
);

CREATE TABLE IF NOT EXISTS dq_results (
  run_id INTEGER NOT NULL,
  rule_id TEXT NOT NULL,
  rule_description TEXT NOT NULL,
  severity TEXT NOT NULL,
  failed_count INTEGER NOT NULL,
  sample_keys TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY (run_id, rule_id),
  FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS change_log (
  run_id INTEGER NOT NULL,
  change_type TEXT NOT NULL,
  entity_key TEXT NOT NULL,
  country_code TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT,
  detected_at TEXT NOT NULL,
  PRIMARY KEY (run_id, change_type, entity_key),
  FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE VIEW IF NOT EXISTS v_latest_run AS
SELECT run_id
FROM runs
WHERE status = 'ok'
ORDER BY run_id DESC
LIMIT 1;

CREATE VIEW IF NOT EXISTS v_latest_services AS
SELECT s.*
FROM tsp_services s
JOIN v_latest_run lr ON lr.run_id = s.run_id;

CREATE VIEW IF NOT EXISTS v_latest_dq AS
SELECT d.*
FROM dq_results d
JOIN v_latest_run lr ON lr.run_id = d.run_id;
