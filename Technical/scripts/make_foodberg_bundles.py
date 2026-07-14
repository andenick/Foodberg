#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_foodberg_bundles.py — build the Foodberg CDF data bundle.

Reads the LIVE foodberg.db, exports the curated tables the site features
(prices history, composite indices, economic indicators, retail prices,
WASDE supply & demand, and a US+World PS&D extract) to CSV + Parquet
(no JSON — DNA), assembles a data dictionary + PROVENANCE + LICENSE +
README, writes a bundle_manifest.json, then hands off to the kit
make_bundles.py to produce a byte-reproducible foodberg-data.zip plus a
BUNDLE_MANIFEST.csv (the single source of truth for the on-site size label).

Curated scope (stated honestly in README + PROVENANCE): wasde_psd is filtered
to the United States + World rows (the balance-sheet geographies the Supply &
Demand page features); every other curated table is exported in full. The full
2M-row wasde_psd and the raw DB are NOT shipped — this is a curated research
extract, not a database dump.

Run INSIDE the foodberg-backend container (has the DB + pandas + pyarrow):
    python /tmp/make_foodberg_bundles.py \
        --db /app/data/foodberg.db \
        --workdir /tmp/fb_bundle \
        --make-bundles /tmp/make_bundles.py \
        --out /tmp/foodberg-data.zip
"""
import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import sqlite3

# (table, sql, description) — curated set the site features.
CURATED = [
    ("global_prices",
     "SELECT * FROM global_prices",
     "Monthly global commodity spot prices and indices (Alpha Vantage / FAO / "
     "World Bank), per commodity, with source and unit."),
    ("composite_indices",
     "SELECT * FROM composite_indices",
     "Computed composite food-price indices (FAO- and BLS-family) with base "
     "period and component weights."),
    ("economic_indicators",
     "SELECT * FROM economic_indicators",
     "Macro / food-economic indicator series (FRED, BLS, FAO CPI) with series "
     "id, category and frequency."),
    ("retail_prices",
     "SELECT * FROM retail_prices",
     "Retail food-item prices by store type and location."),
    ("wasde_data",
     "SELECT * FROM wasde_data",
     "USDA WASDE supply & demand estimates: per-commodity statistics "
     "(production, price received, stocks) by year, location and category."),
    ("psd_us_world",
     "SELECT * FROM wasde_psd WHERE country IN ('United States','World')",
     "USDA FAS PS&D (Production, Supply & Distribution) extract — the United "
     "States + World balance-sheet rows (marketing-year, per attribute). "
     "Curated subset of the full ~2M-row wasde_psd table."),
]

LICENSE_TEXT = """Creative Commons Attribution 4.0 International (CC BY 4.0)

You are free to share and adapt this data for any purpose, provided you give
appropriate credit. This bundle is a curated research extract assembled by
Foodberg (foodberg.org). The underlying series are compiled from public
authorities — USDA (WASDE, NASS, FAS PS&D), FAO, FRED/BLS, and the World Bank
Pink Sheet. Defer to each named upstream source (see PROVENANCE.csv and each
row's `source` column) as the authoritative record. Foodberg is an educational
research tool, not an official statistical agency.

Full license text: https://creativecommons.org/licenses/by/4.0/legalcode
"""


def export_tables(con, workdir: Path):
    tables_dir = workdir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    dict_rows = []
    manifest_files = []
    counts = {}
    for name, sql, desc in CURATED:
        df = pd.read_sql_query(sql, con)
        counts[name] = len(df)
        csv_path = tables_dir / f"{name}.csv"
        pq_path = tables_dir / f"{name}.parquet"
        df.to_csv(csv_path, index=False)
        df.to_parquet(pq_path, index=False)
        manifest_files.append({"src": str(csv_path), "arcname": f"tables/{name}.csv"})
        manifest_files.append({"src": str(pq_path), "arcname": f"tables/{name}.parquet"})
        for col in df.columns:
            dict_rows.append({
                "table": name,
                "column": col,
                "dtype": str(df[col].dtype),
                "table_description": desc,
            })
    return dict_rows, manifest_files, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--make-bundles", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    workdir = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(args.db)

    dict_rows, manifest_files, counts = export_tables(con, workdir)
    con.close()

    # data_dictionary.csv
    dd = pd.DataFrame(dict_rows, columns=["table", "column", "dtype", "table_description"])
    dd_path = workdir / "data_dictionary.csv"
    dd.to_csv(dd_path, index=False)

    # PROVENANCE.csv (our own artifact)
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    prov = pd.DataFrame([
        {"table": "global_prices", "rows": counts.get("global_prices"),
         "upstream": "Alpha Vantage / FAO / World Bank", "defer_to": "named source per row",
         "url": "https://www.fao.org/faostat/ ; https://www.worldbank.org/commodities"},
        {"table": "composite_indices", "rows": counts.get("composite_indices"),
         "upstream": "Computed by Foodberg from FAO/BLS components", "defer_to": "FAO / BLS source series",
         "url": "https://www.fao.org/worldfoodsituation/foodpricesindex"},
        {"table": "economic_indicators", "rows": counts.get("economic_indicators"),
         "upstream": "FRED / BLS / FAO", "defer_to": "FRED / BLS",
         "url": "https://fred.stlouisfed.org"},
        {"table": "retail_prices", "rows": counts.get("retail_prices"),
         "upstream": "Retail price collectors", "defer_to": "source column",
         "url": ""},
        {"table": "wasde_data", "rows": counts.get("wasde_data"),
         "upstream": "USDA WASDE / NASS", "defer_to": "USDA",
         "url": "https://www.usda.gov/oce/commodity/wasde"},
        {"table": "psd_us_world", "rows": counts.get("psd_us_world"),
         "upstream": "USDA FAS PS&D (US + World extract)", "defer_to": "USDA FAS",
         "url": "https://apps.fas.usda.gov/psdonline/"},
    ], columns=["table", "rows", "upstream", "defer_to", "url"])
    prov["built_utc"] = built
    prov_path = workdir / "PROVENANCE.csv"
    prov.to_csv(prov_path, index=False)

    # LICENSE
    lic_path = workdir / "LICENSE"
    lic_path.write_text(LICENSE_TEXT, encoding="utf-8")

    # README.md
    total_rows = sum(v for v in counts.values() if v)
    readme = (
        "# Foodberg data bundle\n\n"
        f"Curated research extract from foodberg.org — built {built} (UTC).\n\n"
        "This is a **curated** subset of Foodberg's database: the tables the site "
        "features, exported as CSV + Parquet. It is not a full database dump. The "
        "PS&D table is filtered to the United States + World balance-sheet rows.\n\n"
        "## Tables\n\n"
        + "".join(f"- `tables/{n}` — {c:,} rows\n" for n, c in counts.items())
        + f"\nTotal curated rows: {total_rows:,}\n\n"
        "## Files\n"
        "- `tables/*.csv`, `tables/*.parquet` — the curated data (CSV + Parquet, no JSON)\n"
        "- `data_dictionary.csv` — column-level dictionary\n"
        "- `PROVENANCE.csv` — per-table upstream authority + defer-to\n"
        "- `LICENSE` — CC BY 4.0\n\n"
        "Defer to each named upstream source (USDA, FAO, FRED/BLS, World Bank) as "
        "the authoritative record. Foodberg is an educational research tool.\n"
    )
    readme_path = workdir / "README.md"
    readme_path.write_text(readme, encoding="utf-8")

    # bundle_manifest.json for make_bundles.py
    manifest_files.append({"src": str(readme_path), "arcname": "README.md"})
    manifest = {
        "name": "foodberg-data",
        "license": str(lic_path),
        "dictionary": str(dd_path),
        "provenance": str(prov_path),
        "files": manifest_files,
    }
    import json
    man_path = workdir / "bundle_manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Hand off to the kit make_bundles.py
    rc = subprocess.call([
        sys.executable, args.make_bundles,
        "--manifest", str(man_path), "--out", args.out,
    ])
    if rc != 0:
        print(f"make_bundles.py failed rc={rc}", file=sys.stderr)
        sys.exit(rc)
    print("BUNDLE_OK", args.out)
    for n, c in counts.items():
        print(f"  {n}: {c} rows")


if __name__ == "__main__":
    main()
