from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Config:
    db_path: Path = Path("eidastl.sqlite")
    schema_path: Path = Path("sql/schema.sql")
    raw_dir: Path = Path("data_raw")
    lotl_url: str = "https://ec.europa.eu/tools/lotl/eu-lotl.xml"
    countries: tuple[str, ...] = ("HR", "SI", "DE")
