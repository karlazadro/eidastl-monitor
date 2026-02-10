import os
from dataclasses import dataclass
from pathlib import Path


def _parse_countries(env_value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if not env_value:
        return default
    parts = [c.strip().upper() for c in env_value.split(",")]
    return tuple([c for c in parts if c])


@dataclass(frozen=True)
class Config:
    db_path: Path = Path("eidastl.sqlite")
    schema_path: Path = Path("sql/schema.sql")
    raw_dir: Path = Path("data_raw")
    lotl_url: str = "https://ec.europa.eu/tools/lotl/eu-lotl.xml"
    countries: tuple[str, ...] = ("HR", "SI", "DE")

    @classmethod
    def from_env(cls) -> "Config":
        default = cls().countries
        countries = _parse_countries(os.getenv("COUNTRIES"), default)
        return cls(countries=countries)