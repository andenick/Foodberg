#!/usr/bin/env python3
"""L02 — Fetch FAOSTAT bulk downloads (producer prices + consumer price indices).

Source (public, keyless, CC BY 4.0):
    https://fenixservices.fao.org/faostat/static/bulkdownloads/Prices_E_All_Data_(Normalized).zip
    https://fenixservices.fao.org/faostat/static/bulkdownloads/ConsumerPriceIndices_E_All_Data_(Normalized).zip

WARNING: each zip is tens of MB and expands to ~200-400 MB of CSV. This loader
prints sizes before downloading; run it with --check first if you are on a
metered connection.

Output:
    data/raw/faostat/Prices_E_All_Data_(Normalized).zip
    data/raw/faostat/ConsumerPriceIndices_E_All_Data_(Normalized).zip
    data/raw/faostat/*.csv                      (unzipped)
    data/raw/faostat/*.fetch_meta.json
"""

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import RAW, http_get, write_fetch_meta  # noqa: E402

FILES = {
    "Prices_E_All_Data_(Normalized).zip":
        "https://fenixservices.fao.org/faostat/static/bulkdownloads/"
        "Prices_E_All_Data_(Normalized).zip",
    "ConsumerPriceIndices_E_All_Data_(Normalized).zip":
        "https://fenixservices.fao.org/faostat/static/bulkdownloads/"
        "ConsumerPriceIndices_E_All_Data_(Normalized).zip",
}
DEST_DIR = RAW / "faostat"


def check() -> int:
    import urllib.request
    from _shared import UA
    for name, url in FILES.items():
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                print(f"[L02] {name}: {r.headers.get('Content-Length', '?')} bytes, "
                      f"Last-Modified {r.headers.get('Last-Modified', '?')}")
        except Exception as e:  # noqa: BLE001
            print(f"[L02] {name}: HEAD failed — {e}")
    return 0


def fetch() -> int:
    for name, url in FILES.items():
        dest = DEST_DIR / name
        if dest.exists() and dest.stat().st_size > 1_000_000:
            print(f"[L02] {name} already present ({dest.stat().st_size:,} bytes) — skipping")
        else:
            print(f"[L02] downloading {name} …")
            http_get(url, dest, timeout=900)
            write_fetch_meta(dest, url)
            print(f"[L02] saved {dest} ({dest.stat().st_size:,} bytes)")
        # unzip
        csv_path = dest.with_suffix(".csv")
        if not csv_path.exists():
            print(f"[L02] unzipping to {csv_path.name} …")
            with zipfile.ZipFile(dest) as z:
                member = [m for m in z.namelist() if m.lower().endswith(".csv")][0]
                with z.open(member) as src, open(csv_path, "wb") as out:
                    while True:
                        chunk = src.read(1 << 20)
                        if not chunk:
                            break
                        out.write(chunk)
            print(f"[L02] unzipped -> {csv_path} ({csv_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    sys.exit(fetch())
