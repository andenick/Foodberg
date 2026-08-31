#!/usr/bin/env python3
"""P07 — Harmonise USDA NASS QuickStats JSON into the WASDE family CSV.

Input:  data/raw/nass/<commodity>.json  (list of QuickStats records; from L07)
Output: data/final/usda_nass_wasde.csv — one row per observation:
        commodity, statistic_category, location, agg_level, year,
        reference_period, value, unit, short_desc

NASS 'Value' strings are parsed exactly as the deployed site parses them:
commas stripped; ranges ('2.50-3.00') take the midpoint; publication
suppression codes (D)/(S)/(NA)/(Z)/(X) and blanks become no row — never a
zero, never an imputed value.
"""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import RAW, FINAL  # noqa: E402

SRC_DIR = RAW / "nass"
DEST = FINAL / "usda_nass_wasde.csv"

SUPPRESSED = {"(D)", "(S)", "(NA)", "(Z)", "(X)", "", "None", "(H)"}


def numeric(value_str):
    if value_str is None:
        return None
    s = str(value_str).replace(",", "").strip()
    if s in SUPPRESSED:
        return None
    # publisher ranges: midpoint
    if "-" in s and not s.startswith("-"):
        parts = s.split("-")
        try:
            return (float(parts[0]) + float(parts[1])) / 2
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def main() -> int:
    files = sorted(SRC_DIR.glob("*.json"))
    files = [f for f in files if not f.name.endswith(".fetch_meta.json")]
    if not files:
        print("[P07] no NASS JSON found — run L07 with NASS_API_KEY set "
              "(optional family; skipping)", file=sys.stderr)
        return 3
    DEST.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(DEST, "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        w.writerow(["commodity", "statistic_category", "location", "agg_level",
                    "year", "reference_period", "value", "unit", "short_desc"])
        for fp in files:
            for r in json.loads(fp.read_text(encoding="utf-8")):
                v = numeric(r.get("Value", r.get("value")))
                if v is None:
                    continue
                w.writerow([
                    (r.get("commodity_desc") or "").upper(),
                    r.get("statisticcat_desc", ""),
                    r.get("location_desc", r.get("state_name", "Unknown")),
                    r.get("agg_level_desc", ""),
                    r.get("year", ""),
                    r.get("reference_period_desc", ""),
                    v,
                    r.get("unit_desc", ""),
                    r.get("short_desc", ""),
                ])
                n += 1
    print(f"[P07] usda_nass_wasde.csv: {n} rows -> {DEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
