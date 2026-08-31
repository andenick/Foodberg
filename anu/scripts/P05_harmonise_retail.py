#!/usr/bin/env python3
"""P05 — Harmonise BLS Average Price series into per-series retail CSVs.

Input:  data/raw/blsap/<APU_ID>.csv  (fredgraph.csv mirror of the APU series)
Output: data/final/retail/<APU_ID>.csv — columns: date, price, unit, area.

Unit and area come from series_registry.json (the registry is the data
contract); prices are the publisher's average, verbatim. Missing '.' values
are dropped, never imputed.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import RAW, FINAL, load_registry  # noqa: E402

SRC_DIR = RAW / "blsap"
DEST_DIR = FINAL / "retail"


def main() -> int:
    if not SRC_DIR.exists():
        print(f"[P05] missing {SRC_DIR} — run L06 first", file=sys.stderr)
        return 1
    reg_units = {s["series_id"]: s.get("units", "") for s in load_registry()["series"]}
    reg_area = {s["series_id"]: s["description"] for s in load_registry()["series"]}
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for src in sorted(SRC_DIR.glob("*.csv")):
        sid = src.stem
        rows = []
        with src.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                date = (r.get("observation_date") or "").strip()
                raw = (r.get(sid) or "").strip()
                if not date or raw in ("", "."):
                    continue
                try:
                    rows.append((date, float(raw)))
                except ValueError:
                    continue
        rows.sort(key=lambda r: r[0])
        # area: parsed from the registry description (US average unless the
        # description names a Census region)
        area = "U.S. city average"
        desc = reg_area.get(sid, "")
        for region in ("Northeast", "Midwest", "South", "West"):
            if region in desc:
                area = f"{region} region"
                break
        unit = reg_units.get(sid, "")
        dest = DEST_DIR / f"{sid}.csv"
        with open(dest, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date", "price", "unit", "area"])
            w.writerows((d, p, unit, area) for d, p in rows)
        span = f"{rows[0][0]}..{rows[-1][0]}" if rows else "EMPTY"
        print(f"[P05] {sid}: {len(rows)} obs ({span}) [{unit}]")
        n += 1
    print(f"[P05] wrote {n} retail series to {DEST_DIR}")
    return 0 if n else 1


if __name__ == "__main__":
    sys.exit(main())
