"""Shared helpers for the Foodberg replication pipeline.

Every path in this package is relative to the ``anu/`` directory that contains
this module's parent — the package is fully relocatable and never references
anything outside itself.
"""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent          # .../anu
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FINAL = ROOT / "data" / "final"
REGISTRY = ROOT / "series_registry.json"

# Some hosts reject default urllib user agents; a plain client id works.
UA = "FoodbergReplication/1.0 (+https://github.com/andenick/Foodberg)"


def ensure_dirs() -> None:
    for d in (RAW, PROCESSED, FINAL):
        d.mkdir(parents=True, exist_ok=True)


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def http_get(url: str, dest: Path, attempts: int = 4, timeout: int = 120,
             ua: str = UA) -> Path:
    """GET ``url`` and stream it to ``dest`` with retry + backoff.

    Raises on final failure — no silent fallbacks.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err: Optional[Exception] = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
                while True:
                    chunk = r.read(1 << 16)
                    if not chunk:
                        break
                    f.write(chunk)
            return dest
        except Exception as e:  # noqa: BLE001 — retry any transport error
            last_err = e
            if i < attempts - 1:
                time.sleep(10 * (i + 1))
    raise RuntimeError(f"GET failed after {attempts} attempts: {url} ({last_err})")


def write_fetch_meta(dest: Path, url: str, **extra) -> None:
    """Sidecar recording where/when a raw artifact came from."""
    meta = dest.parent / f"{dest.name}.fetch_meta.json"
    meta.write_text(json.dumps({"url": url, **extra}, indent=2), encoding="utf-8")


def slugify(name: str) -> str:
    """Series-id slug used for Pink Sheet columns (must match the registry)."""
    import re
    s = name.replace("**", "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")
