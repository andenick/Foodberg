#!/usr/bin/env python3
"""L07 — Fetch USDA NASS QuickStats history for WASDE commodities (OPTIONAL).

Source (public; FREE API key required):
    https://quickstats.nass.usda.gov/api
    Register for a key at https://quickstats.nass.usda.gov/api — instant,
    free. Provide it via the NASS_API_KEY environment variable.

Queries, per commodity: statisticcat_desc in (PRICE RECEIVED, PRODUCTION,
YIELD) with agg_level_desc=NATIONAL (add --states for the top-15 state
detail). This mirrors the categories the deployed site bakes from the NASS
annual history.

This loader is OPTIONAL for the package: without a key it prints instructions
and exits 3, and the validator treats the family as absent-but-allowed.

Output: data/raw/nass/<commodity>.json (+ .fetch_meta.json)
"""

import json
import os
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import RAW, write_fetch_meta, UA  # noqa: E402

API = "https://quickstats.nass.usda.gov/api/api_get/"
DEST_DIR = RAW / "nass"

COMMODITIES = [
    "almonds", "apples", "avocados", "barley", "beef", "blueberries", "canola",
    "cattle", "chickens", "corn", "cotton", "cranberries", "eggs", "flaxseed",
    "grapes", "hay", "hazelnuts", "hogs", "honey", "lentils", "milk", "millet",
    "mohair", "mushrooms", "oats", "oranges", "peanuts", "peas", "pecans",
    "pistachios", "pork", "potatoes", "rapeseed", "rice", "rye", "safflower",
    "sheep", "sorghum", "soybeans", "strawberries", "sugarcane", "sunflower",
    "sweet potatoes", "tobacco", "turkeys", "walnuts", "wheat", "wool",
]
CATEGORIES = ["PRICE RECEIVED", "PRODUCTION", "YIELD"]


def fetch(commodity: str, key: str, agg_levels: list) -> list:
    rows = []
    for agg in agg_levels:
        params = {
            "key": key,
            "commodity_desc": commodity,
            "statisticcat_desc": ",".join(CATEGORIES),
            "agg_level_desc": agg,
            "format": "JSON",
        }
        url = API + "?" + urllib.parse.urlencode(params)
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=300) as r:
            payload = json.loads(r.read().decode())
        rows.extend(payload.get("data", []))
    return rows


def main() -> int:
    key = os.environ.get("NASS_API_KEY", "").strip()
    if not key:
        print("[L07] NASS_API_KEY not set. This optional loader is skipped.")
        print("       Get a free key at https://quickstats.nass.usda.gov/api "
              "and re-run with NASS_API_KEY=<key>.")
        return 3
    agg_levels = ["NATIONAL", "STATE"] if "--states" in sys.argv else ["NATIONAL"]
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for commodity in COMMODITIES:
        dest = DEST_DIR / f"{commodity}.json"
        if dest.exists():
            total += len(json.loads(dest.read_text(encoding="utf-8")))
            continue
        rows = fetch(commodity, key, agg_levels)
        dest.write_text(json.dumps(rows, indent=1), encoding="utf-8")
        write_fetch_meta(dest, API, commodity=commodity, agg_levels=agg_levels)
        print(f"[L07] {commodity}: {len(rows)} records")
        total += len(rows)
    print(f"[L07] total NASS records: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
