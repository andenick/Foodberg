#!/usr/bin/env python3
"""P02 — Harmonise FAOSTAT bulk CSVs into the two family outputs.

Input:
    data/raw/faostat/Prices_E_All_Data_(Normalized).csv
    data/raw/faostat/ConsumerPriceIndices_E_All_Data_(Normalized).csv

Output:
    data/final/faostat_producer_prices.csv
        columns: series_id (PP_<item_code>), country, item, year, date,
                 value_usd_tonne
        filter:  Element == 'Producer Price (USD/tonne)' AND
                 Months == 'Annual value'
    data/final/faostat_food_cpi.csv
        columns: series_id, country, item, date (YYYY-MM-01), value
        filter:  Item Code == 23013 (Consumer Prices, Food Indices, 2015=100)
                 with a real calendar month

Values are copied verbatim from the bulk download; nothing is imputed.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import RAW, FINAL  # noqa: E402

PRICES_CSV = RAW / "faostat" / "Prices_E_All_Data_(Normalized).csv"
CPI_CSV = RAW / "faostat" / "ConsumerPriceIndices_E_All_Data_(Normalized).csv"

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}

BATCH = 50_000


def numeric(s):
    if s is None:
        return None
    t = str(s).replace(",", "").strip()
    if t in ("", "...", "-", "F", "None", "(NA)"):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def producer_prices() -> int:
    if not PRICES_CSV.exists():
        print(f"[P02] missing {PRICES_CSV} — run L02 first", file=sys.stderr)
        return 1
    dest = FINAL / "faostat_producer_prices.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with PRICES_CSV.open(encoding="utf-8-sig", newline="") as f, \
            open(dest, "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        w.writerow(["series_id", "country", "item", "year", "date",
                    "value_usd_tonne"])
        batch = []
        for r in csv.DictReader(f):
            if r["Element"] != "Producer Price (USD/tonne)":
                continue
            if r["Months"] != "Annual value":
                continue
            v = numeric(r["Value"])
            if v is None:
                continue
            batch.append((f"PP_{r['Item Code']}", r["Area"], r["Item"],
                          r["Year"], f"{int(r['Year']):04d}-07-01", v))
            if len(batch) >= BATCH:
                w.writerows(batch)
                n += len(batch)
                batch = []
        w.writerows(batch)
        n += len(batch)
    print(f"[P02] faostat_producer_prices.csv: {n} rows -> {dest}")
    return 0


def food_cpi() -> int:
    if not CPI_CSV.exists():
        print(f"[P02] missing {CPI_CSV} — run L02 first", file=sys.stderr)
        return 1
    dest = FINAL / "faostat_food_cpi.csv"
    n = 0
    with CPI_CSV.open(encoding="utf-8-sig", newline="") as f, \
            open(dest, "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        w.writerow(["series_id", "country", "item", "date", "value"])
        batch = []
        for r in csv.DictReader(f):
            if r["Item Code"] != "23013":
                continue
            month = MONTHS.get(r.get("Months", ""))
            if month is None:
                continue
            v = numeric(r["Value"])
            if v is None:
                continue
            batch.append(("FAO_CPI_FOOD", r["Area"], r["Item"],
                          f"{int(r['Year']):04d}-{month:02d}-01", v))
            if len(batch) >= BATCH:
                w.writerows(batch)
                n += len(batch)
                batch = []
        w.writerows(batch)
        n += len(batch)
    print(f"[P02] faostat_food_cpi.csv: {n} rows -> {dest}")
    return 0


if __name__ == "__main__":
    rc = producer_prices()
    rc2 = food_cpi()
    sys.exit(rc or rc2)
