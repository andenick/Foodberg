#!/usr/bin/env python3
"""L03 — Fetch the FAO Food Price Index (monthly, 1990-present).

Source (public, keyless, CC BY 4.0):
    https://www.fao.org/worldfoodsituation/foodpricesindex/en/
    -> "food_price_indices_data.csv" (columns: Date, Food Price Index, Meat,
       Dairy, Cereals, Oils, Sugar; base 2014-2016=100)

Strategy: scrape the landing page for the current CSV href (the document
library appends a rotating hash), falling back to the pinned URL verified
live in 2026-08.

Output:
    data/raw/fao_fpi/food_price_indices_data.csv
    data/raw/fao_fpi/food_price_indices_data.csv.fetch_meta.json
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import RAW, http_get, write_fetch_meta, UA  # noqa: E402

LANDING = "https://www.fao.org/worldfoodsituation/foodpricesindex/en/"
PINNED_URL = (
    "https://www.fao.org/media/docs/worldfoodsituationlibraries/"
    "default-document-library/food_price_indices_data.csv"
    "?sfvrsn=523ebd2a_82&download=true"
)
DEST = RAW / "fao_fpi" / "food_price_indices_data.csv"


def scrape_current_url() -> str:
    import urllib.request
    req = urllib.request.Request(LANDING, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        html = r.read().decode("utf-8", errors="replace")
    html = html.replace("&amp;", "&")
    hits = re.findall(r'href="([^"]*food_price_indices_data\.csv[^"]*)"', html)
    if not hits:
        raise RuntimeError("No food_price_indices_data.csv link on the landing page")
    return hits[0]


def main() -> int:
    url_used = PINNED_URL
    try:
        http_get(PINNED_URL, DEST)
        text = DEST.read_text(encoding="utf-8", errors="replace")
        if "Food Price Index" not in text or "1990-01" not in text:
            raise RuntimeError("pinned URL did not return the expected CSV")
    except Exception as e:  # noqa: BLE001
        print(f"[L03] pinned URL failed ({e}); scraping landing page …")
        DEST.unlink(missing_ok=True)
        url_used = scrape_current_url()
        http_get(url_used, DEST)

    n = sum(1 for _ in DEST.open(encoding="utf-8"))
    write_fetch_meta(DEST, url_used)
    print(f"[L03] FAO FPI saved: {DEST} ({n} lines) from {url_used}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
