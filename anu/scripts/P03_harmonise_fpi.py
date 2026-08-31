#!/usr/bin/env python3
"""P03 — Harmonise the FAO Food Price Index CSV into per-series outputs.

Input:  data/raw/fao_fpi/food_price_indices_data.csv
Output: data/final/fpi/fao_fpi_<cat>.csv — columns: date (YYYY-MM-01), value.

The publisher's columns map 1:1 onto registry series:
    Food Price Index -> fao_fpi_overall, Meat -> fao_fpi_meat,
    Dairy -> fao_fpi_dairy, Cereals -> fao_fpi_cereals,
    Oils -> fao_fpi_oils, Sugar -> fao_fpi_sugar.
FAO's chained index is passed through VERBATIM — never recomputed here.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import RAW, FINAL  # noqa: E402

SRC = RAW / "fao_fpi" / "food_price_indices_data.csv"
DEST_DIR = FINAL / "fpi"

COLMAP = {
    "Food Price Index": "fao_fpi_overall",
    "Meat": "fao_fpi_meat",
    "Dairy": "fao_fpi_dairy",
    "Cereals": "fao_fpi_cereals",
    "Oils": "fao_fpi_oils",
    "Sugar": "fao_fpi_sugar",
}


def main() -> int:
    if not SRC.exists():
        print(f"[P03] missing {SRC} — run L03 first", file=sys.stderr)
        return 1
    # The publisher's CSV has 4 preamble lines before the header row.
    text = SRC.read_text(encoding="utf-8-sig").splitlines()
    hdr_i = next(i for i, l in enumerate(text)
                 if l.startswith("Date") and "Food Price Index" in l)
    reader = csv.DictReader(text[hdr_i:])
    series: dict = {sid: [] for sid in COLMAP.values()}
    for row in reader:
        date = (row.get("Date") or "").strip()
        if len(date) != 7 or date[4] != "-":
            continue
        for col, sid in COLMAP.items():
            raw = (row.get(col) or "").strip()
            if not raw:
                continue
            try:
                series[sid].append((f"{date}-01", float(raw)))
            except ValueError:
                continue
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    for sid, rows in series.items():
        rows.sort(key=lambda r: r[0])
        dest = DEST_DIR / f"{sid}.csv"
        with open(dest, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date", "value"])
            w.writerows(rows)
        print(f"[P03] {sid}: {len(rows)} obs "
              f"({rows[0][0]}..{rows[-1][0]})" if rows else f"[P03] {sid}: EMPTY")
    return 0


if __name__ == "__main__":
    sys.exit(main())
