#!/usr/bin/env python3
"""L04 — Fetch FRED indicator series (keyless fredgraph.csv mirror).

Source (public, keyless):
    https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID>

Every series used by the site's economic-indicator family. fredgraph.csv is
FRED's documented no-key CSV endpoint: the full published history of a series,
one row per observation, missing values as '.'.

Output: data/raw/fred/<SERIES_ID>.csv (+ .fetch_meta.json)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import RAW, http_get, write_fetch_meta  # noqa: E402

# (series_id, why it is in the package)
FRED_IDS = {
    "CPIAUCSL": "headline CPI (context)",
    "CPIUFDSL": "CPI food",
    "CUSR0000SAF11": "CPI food at home",
    "CUSR0000SAF111": "CPI cereals & bakery",
    "CUSR0000SAF112": "CPI meats/poultry/fish/eggs",
    "CUSR0000SAF113": "CPI fruits & vegetables",
    "CUSR0000SEFJ": "CPI dairy",
    "CUSR0000SEFV": "CPI food away from home",
    "FEDFUNDS": "effective federal funds rate",
    "UNRATE": "unemployment rate",
    "WPU01": "PPI farm products",
    "WPU02": "PPI processed foods and feeds",
    "WPU01130217": "PPI wheat",
    "GDPDEF": "GDP implicit price deflator (the project's only real-terms deflator)",
}

BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
DEST_DIR = RAW / "fred"


def main() -> int:
    failures = []
    for sid, why in FRED_IDS.items():
        dest = DEST_DIR / f"{sid}.csv"
        if dest.exists() and dest.stat().st_size > 100:
            print(f"[L04] {sid} present — skipping")
            continue
        url = BASE.format(sid=sid)
        try:
            http_get(url, dest, ua="curl/8.0")  # FRED rejects some python UAs
            head = dest.read_text(encoding="utf-8", errors="replace").splitlines()[0]
            if sid not in head:
                raise RuntimeError(f"unexpected header: {head[:80]!r}")
            write_fetch_meta(dest, url)
            print(f"[L04] {sid} ({why}) — {dest.stat().st_size:,} bytes")
        except Exception as e:  # noqa: BLE001
            print(f"[L04] FAIL {sid}: {e}", file=sys.stderr)
            failures.append(sid)
    if failures:
        print(f"[L04] failed series: {failures}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
