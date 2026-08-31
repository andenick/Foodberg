#!/usr/bin/env python3
"""P06 — Construct the two Foodberg composite indices.

Outputs:
    data/final/composites/foodberg_global_composite.csv
    data/final/composites/bls_overall.csv

Method (mirrors the deployed site's computation exactly):

  foodberg_global_composite — fixed-weight average of the five FAO
  sub-indices (fao_fpi_*): meat 0.348, cereals 0.272, dairy 0.173,
  oils 0.135, sugar 0.072. Computed for every month with >= 4 of 5
  components present; weights renormalized over present components;
  rounded to 2 decimals. This is a FOODBERG CONSTRUCTION — it is not the
  FAO Food Price Index (which is chained with trade-share weights) and
  must never be labelled as such.

  bls_overall — fixed-weight average of five BLS CPI-U (NSA) food
  components: CUUR0000SAF112 (meats .30), CUUR0000SAF111 (cereals .20),
  CUUR0000SAF113 (produce .18), CUUR0000SEFV (food away .17),
  CUUR0000SEFJ (dairy .15). Computed for every month with >= 3 of 5
  components present; weights renormalized; rounded to 2 decimals. BLS
  publishes no such index.

Inputs are the P03/P04 outputs — this script reads nothing raw.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import FINAL  # noqa: E402

FPI_DIR = FINAL / "fpi"
IND_DIR = FINAL / "indicators"
DEST_DIR = FINAL / "composites"

FAO_WEIGHTS = {
    "fao_fpi_meat": 0.348,
    "fao_fpi_cereals": 0.272,
    "fao_fpi_dairy": 0.173,
    "fao_fpi_oils": 0.135,
    "fao_fpi_sugar": 0.072,
}
FAO_MIN = 4

BLS_WEIGHTS = {
    "CUUR0000SAF112": 0.30,
    "CUUR0000SAF111": 0.20,
    "CUUR0000SAF113": 0.18,
    "CUUR0000SEFV": 0.17,
    "CUUR0000SEFJ": 0.15,
}
BLS_MIN = 3


def read_series(path: Path) -> dict:
    """{YYYY-MM: float} from a date,value CSV."""
    out = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            d = (r.get("date") or "")[:7]
            if len(d) == 7:
                try:
                    out[d] = float(r["value"])
                except (TypeError, ValueError):
                    continue
    return out


def composite(weights: dict, data: dict, min_components: int) -> list:
    all_dates = sorted(set().union(*[set(v) for v in data.values()]))
    rows = []
    for d in all_dates:
        present = {sid: data[sid][d] for sid in weights
                   if d in data.get(sid, {})}
        if len(present) < min_components:
            continue
        wsum = sum(weights[sid] for sid in present)
        value = sum(weights[sid] * v for sid, v in present.items()) / wsum
        rows.append((f"{d}-01", round(value, 2), len(present)))
    return rows


def write(name: str, rows: list) -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    dest = DEST_DIR / f"{name}.csv"
    with open(dest, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "value", "n_components"])
        w.writerows(rows)
    span = f"{rows[0][0]}..{rows[-1][0]}" if rows else "EMPTY"
    print(f"[P06] {name}: {len(rows)} months ({span}) -> {dest}")


def main() -> int:
    fao_data = {sid: read_series(FPI_DIR / f"{sid}.csv") for sid in FAO_WEIGHTS}
    if any(not v for v in fao_data.values()):
        missing = [s for s, v in fao_data.items() if not v]
        print(f"[P06] missing FAO inputs {missing} — run L03+P03 first",
              file=sys.stderr)
        return 1
    write("foodberg_global_composite", composite(FAO_WEIGHTS, fao_data, FAO_MIN))

    bls_data = {sid: read_series(IND_DIR / f"{sid}.csv") for sid in BLS_WEIGHTS}
    if any(not v for v in bls_data.values()):
        missing = [s for s, v in bls_data.items() if not v]
        print(f"[P06] missing BLS inputs {missing} — run L05+P04 first",
              file=sys.stderr)
        return 1
    write("bls_overall", composite(BLS_WEIGHTS, bls_data, BLS_MIN))
    return 0


if __name__ == "__main__":
    sys.exit(main())
