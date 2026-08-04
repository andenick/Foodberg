#!/usr/bin/env python3
"""
process_psd_wasde.py
====================
Normalize the USDA FAS PS&D (Production, Supply & Distribution) bulk CSVs into a
tidy long WASDE-style balance-sheet dataset, then load it into the Foodberg DB.

Source (official, machine-readable, reachable):
    https://apps.fas.usda.gov/psdonline/downloads/psd_<group>_csv.zip
PS&D is the canonical machine-readable supply/demand database that underlies the
WASDE *world* tables; it "incorporates all historical revisions" (USDA FAS) and
covers Market_Year 1960-present for the major commodities. We label it honestly
as PS&D (FAS) -- NOT a verbatim WASDE-report transcription.

Honesty rules (Anu / .claude/rules/anu-framework.md):
  - No fabrication, no interpolation. Missing values stay missing.
  - Every value traces to the source file (source + vintage Month/Calendar_Year recorded).
  - World aggregate is a transparent SUM of reported country values for additive
    attributes ONLY (never for ratios/percent/yield); flagged is_aggregate=1.

Outputs:
  - Per-(commodity x region) tidy CSV + Parquet under Outputs/Data/WASDE_PSD/
  - data_dictionary.csv (attribute -> unit, per commodity type)
  - Loads table `wasde_psd` into backend/data/foodberg.db
"""
from __future__ import annotations
import csv
import sqlite3
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

import pandas as pd

# ---- paths (relative to project root) -------------------------------------
PROJ = Path(__file__).resolve().parents[2]          # repository root
PSD_DIR = PROJ / "Inputs" / "USDA_WASDE_official" / "psd"
OUT_DIR = PROJ / "Outputs" / "Data" / "WASDE_PSD"
DB_PATH = PROJ / "backend" / "data" / "foodberg.db"

SOURCE_LABEL = "USDA FAS PS&D (Production, Supply & Distribution)"
SOURCE_URL = "https://apps.fas.usda.gov/psdonline/downloads/"

# Attributes that are additive across countries (safe to sum into a World total).
# Ratios / percentages / yields / rates are NEVER summed.
NON_ADDITIVE_ATTRS = {
    "Annual % Change Per Cap. Cons.", "Extr. Rate, 999.9999", "Stocks-to-Use",
    "Yield", "Seed to Lint Ratio", "Milling Rate (.9999)",
}
NON_ADDITIVE_UNITS = {"(PERCENT)", "(RATIO)", "(KG/HA)", "(MT/HA)"}

# Commodities to surface as headline Foodberg series (key balance sheets).
# We process ALL commodities; this set only drives the validation print.
KEY_COMMODITIES = {
    "Wheat", "Corn", "Rice, Milled", "Barley", "Sorghum", "Oats",
    "Oilseed, Soybean", "Oil, Soybean", "Meal, Soybean",
    "Cotton", "Sugar, Centrifugal", "Coffee, Green",
    "Meat, Beef and Veal", "Meat, Chicken", "Meat, Swine",
    "Animal Numbers, Cattle", "Dairy, Cheese", "Dairy, Butter",
}


def slug(s: str) -> str:
    return (
        s.lower().replace(",", "").replace("(", "").replace(")", "")
        .replace("/", "-").replace(".", "").replace("&", "and")
        .replace("  ", " ").strip().replace(" ", "_")
    )


def is_additive(attr: str, unit: str) -> bool:
    if attr in NON_ADDITIVE_ATTRS:
        return False
    if unit.strip() in NON_ADDITIVE_UNITS:
        return False
    return True


def read_psd_rows(csv_paths):
    """Yield normalized dict rows from all PS&D CSVs."""
    for p in csv_paths:
        with open(p, encoding="utf-8-sig", newline="") as fh:
            rd = csv.DictReader(fh)
            for r in rd:
                my = r["Market_Year"].strip()
                if not my.isdigit():
                    continue
                val = r["Value"].strip()
                try:
                    num = float(val)
                except ValueError:
                    num = None
                yield {
                    "commodity": r["Commodity_Description"].strip(),
                    "commodity_code": r["Commodity_Code"].strip(),
                    "country": r["Country_Name"].strip(),
                    "country_code": r["Country_Code"].strip(),
                    "market_year": int(my),
                    "calendar_year": (int(r["Calendar_Year"]) if r["Calendar_Year"].strip().isdigit() else None),
                    "vintage_month": r["Month"].strip(),
                    "attribute": r["Attribute_Description"].strip(),
                    "attribute_id": r["Attribute_ID"].strip(),
                    "unit": r["Unit_Description"].strip(),
                    "value": num,
                    "source_file": p.name,
                }


def main():
    csv_paths = sorted(PSD_DIR.glob("psd_*.csv"))
    if not csv_paths:
        sys.exit(f"No PS&D CSVs found in {PSD_DIR}")
    print(f"Reading {len(csv_paths)} PS&D files from {PSD_DIR}")

    rows = list(read_psd_rows(csv_paths))
    print(f"Loaded {len(rows):,} raw PS&D observations")

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["value"])  # missing values stay missing (dropped, not imputed)
    print(f"{len(df):,} observations with a numeric value")

    # ---- build World aggregate for additive attributes -------------------
    add_mask = df.apply(lambda r: is_additive(r["attribute"], r["unit"]), axis=1)
    additive = df[add_mask]
    grp = (
        additive.groupby(
            ["commodity", "commodity_code", "market_year", "attribute",
             "attribute_id", "unit"], as_index=False
        )
        .agg(value=("value", "sum"), n_countries=("country", "nunique"))
    )
    grp["country"] = "World"
    grp["country_code"] = "WLD"
    grp["calendar_year"] = None
    grp["vintage_month"] = "agg"
    grp["source_file"] = "DERIVED:sum-of-reported-countries"
    grp["is_aggregate"] = 1
    df["is_aggregate"] = 0
    df["n_countries"] = 1
    world = grp[df.columns]  # align columns

    full = pd.concat([df, world], ignore_index=True)
    full["source"] = SOURCE_LABEL
    full["source_url"] = SOURCE_URL
    full["loaded_at"] = datetime.now(timezone.utc).isoformat()

    print(f"Final long table: {len(full):,} rows "
          f"({(full['is_aggregate']==1).sum():,} World-aggregate rows)")
    print(f"Market_Year span: {full.market_year.min()}-{full.market_year.max()}")
    print(f"Commodities: {full.commodity.nunique()}  Countries(+World): {full.country.nunique()}")

    # ---- write per-(commodity x region: US + World) tidy files -----------
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    regions = {"United States": "us", "World": "world"}
    written = []
    for commod in sorted(full.commodity.unique()):
        for region, rslug in regions.items():
            sub = full[(full.commodity == commod) & (full.country == region)]
            if sub.empty:
                continue
            cols = ["commodity", "country", "market_year", "attribute", "unit",
                    "value", "is_aggregate", "n_countries", "vintage_month",
                    "source", "source_url"]
            sub = sub[cols].sort_values(["attribute", "market_year"])
            base = OUT_DIR / f"wasde_psd_{slug(commod)}__{rslug}"
            sub.to_csv(base.with_suffix(".csv"), index=False)
            sub.to_parquet(base.with_suffix(".parquet"), index=False)
            written.append((commod, region, len(sub)))

    print(f"Wrote {len(written)} per-(commodity x region) CSV+Parquet pairs to {OUT_DIR}")

    # ---- data dictionary -------------------------------------------------
    dd = (
        full.groupby(["commodity", "attribute", "attribute_id", "unit"], as_index=False)
        .size().rename(columns={"size": "n_rows"})
        .sort_values(["commodity", "attribute"])
    )
    dd["additive_across_countries"] = dd.apply(
        lambda r: is_additive(r["attribute"], r["unit"]), axis=1)
    dd.to_csv(OUT_DIR / "data_dictionary.csv", index=False)
    print(f"Wrote data_dictionary.csv ({len(dd)} commodity x attribute rows)")

    # ---- combined long CSV + Parquet (the full dataset) ------------------
    combined_cols = ["commodity", "commodity_code", "country", "country_code",
                     "market_year", "calendar_year", "attribute", "attribute_id",
                     "unit", "value", "is_aggregate", "n_countries",
                     "vintage_month", "source", "source_url"]
    full[combined_cols].to_parquet(OUT_DIR / "wasde_psd_full.parquet", index=False)
    print(f"Wrote wasde_psd_full.parquet ({len(full):,} rows)")

    # ---- load into DB ----------------------------------------------------
    load_db(full[combined_cols])

    # ---- validation print -----------------------------------------------
    print("\n=== VALIDATION: key commodities, World region, Ending Stocks span ===")
    for commod in sorted(KEY_COMMODITIES):
        sub = full[(full.commodity == commod) & (full.country == "World")
                   & (full.attribute.isin(["Ending Stocks", "Production"]))]
        if sub.empty:
            continue
        print(f"  {commod:28} MY {int(sub.market_year.min())}-{int(sub.market_year.max())}  "
              f"rows={len(sub):,}")


def load_db(df: pd.DataFrame):
    print(f"\nLoading table `wasde_psd` into {DB_PATH}")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS wasde_psd")
    cur.execute("""
        CREATE TABLE wasde_psd (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commodity TEXT NOT NULL,
            commodity_code TEXT,
            country TEXT NOT NULL,
            country_code TEXT,
            market_year INTEGER NOT NULL,
            calendar_year INTEGER,
            attribute TEXT NOT NULL,
            attribute_id TEXT,
            unit TEXT,
            value REAL,
            is_aggregate INTEGER DEFAULT 0,
            n_countries INTEGER,
            vintage_month TEXT,
            source TEXT,
            source_url TEXT
        )
    """)
    df.to_sql("wasde_psd", con, if_exists="append", index=False)
    cur.execute("CREATE INDEX idx_psd_commodity ON wasde_psd(commodity)")
    cur.execute("CREATE INDEX idx_psd_country ON wasde_psd(country)")
    cur.execute("CREATE INDEX idx_psd_my ON wasde_psd(market_year)")
    cur.execute("CREATE INDEX idx_psd_cca ON wasde_psd(commodity, country, attribute)")
    con.commit()
    n = cur.execute("SELECT COUNT(*) FROM wasde_psd").fetchone()[0]
    print(f"  wasde_psd rows: {n:,}")
    con.close()


if __name__ == "__main__":
    main()
