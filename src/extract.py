from __future__ import annotations
import requests
from pathlib import Path
from typing import Optional
from .util import sha256_bytes, utc_now_iso

def download(url: str, out_path: Path) -> dict:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    data = r.content

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)

    return {
        "url": url,
        "fetched_at": utc_now_iso(),
        "sha256": sha256_bytes(data),
        "bytes": len(data),
        "path": str(out_path),
    }

def safe_filename(prefix: str, country_code: Optional[str] = None) -> str:
    ts = utc_now_iso().replace(":", "").replace("+", "_")
    if country_code:
        return f"{prefix}_{country_code}_{ts}.xml"
    return f"{prefix}_{ts}.xml"
