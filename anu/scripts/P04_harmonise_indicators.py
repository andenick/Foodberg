#!/usr/bin/env python3
"""P04 — Harmonise FRED + BLS indicator series into per-series CSVs.

Input:
    data/raw/fred/<ID>.csv        (fredgraph.csv: observation_date,<ID>)
    data/raw/bls/<ID>.json        ({"series_id":..., "data":[{date,value}]})

Output: data/final/indicators/<ID>.csv — columns: date, value, source.

Verbatim pass-through: FRED '.' missings are dropped (never imputed), BLS
non-numeric values are dropped, and each observation keeps the publisher's
own date. GDPDEF arrives quarterly; everything else monthly — the registry
records the frequency per series.
"""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import RAW, FINAL  # noqa: E402

FRED_DIR = RAW / "fred"
BLS_DIR = RAW / "bls"
DEST_DIR = FINAL / "indicators"


def main() -> int:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    n_ok = 0
    for src in sorted(FRED_DIR.glob("*.csv")):
        sid = src.stem
        if sid.endswith(".fetch_meta"):
            continue
        rows = []
        with src.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                date = (r.get("observation_date") or "").strip()
                raw = (r.get(sid) or "").strip()
                if not date or raw in ("", "."):
                    continue
                try:
                    rows.append((date, float(raw), "FRED"))
                except ValueError:
                    continue
        _write(sid, rows)
        n_ok += 1
    for src in sorted(BLS_DIR.glob("*.json")):
        if src.name.endswith(".fetch_meta.json"):
            continue
        payload = json.loads(src.read_text(encoding="utf-8"))
        rows = []
        for o in payload.get("data", []):
            try:
                rows.append((o["date"][:10], float(o["value"]), "BLS"))
            except (TypeError, ValueError, KeyError):
                continue
        _write(src.stem, rows)
        n_ok += 1
    print(f"[P04] wrote {n_ok} indicator series to {DEST_DIR}")
    return 0 if n_ok else 1


def _write(sid: str, rows: list) -> None:
    rows.sort(key=lambda r: r[0])
    dest = DEST_DIR / f"{sid}.csv"
    with open(dest, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "value", "source"])
        w.writerows(rows)
    span = f"{rows[0][0]}..{rows[-1][0]}" if rows else "EMPTY"
    print(f"[P04] {sid}: {len(rows)} obs ({span})")


if __name__ == "__main__":
    sys.exit(main())
