#!/usr/bin/env python3
"""L06 — Fetch BLS Average Price (APU) retail food series via FRED (keyless).

Source (public, keyless):
    https://fred.stlouisfed.org/graph/fredgraph.csv?id=<APU_ID>

The BLS Average Price program (APU*) is mirrored in full on FRED, so the
keyless fredgraph.csv endpoint serves it without a BLS key. 47 U.S.-average
items plus 4 Census-region tomato series.

Output: data/raw/blsap/<APU_ID>.csv (+ .fetch_meta.json)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import RAW, http_get, write_fetch_meta  # noqa: E402

APU_IDS = [
    "APU0000701111", "APU0000701312", "APU0000701322", "APU0000702111",
    "APU0000702212", "APU0000702421", "APU0000702611", "APU0000703112",
    "APU0000703212", "APU0000703432", "APU0000703511", "APU0000703613",
    "APU0000704111", "APU0000704212", "APU0000704312", "APU0000704321",
    "APU0000704413", "APU0000706111", "APU0000706212", "APU0000707111",
    "APU0000708111", "APU0000709112", "APU0000709213", "APU0000710111",
    "APU0000710122", "APU0000710212", "APU0000710411", "APU0000711111",
    "APU0000711211", "APU0000711311", "APU0000711412", "APU0000711415",
    "APU0000711417", "APU0000712112", "APU0000712211", "APU0000712311",
    "APU0000712401", "APU0000712403", "APU0000712404", "APU0000712406",
    "APU0000712412", "APU0000713111", "APU0000714233", "APU0000715211",
    "APU0000715212", "APU0000717311", "APU0000718311",
    "APU0100712311", "APU0200712311", "APU0300712311", "APU0400712311",
]

BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
DEST_DIR = RAW / "blsap"


def main() -> int:
    failures = []
    for sid in APU_IDS:
        dest = DEST_DIR / f"{sid}.csv"
        if dest.exists() and dest.stat().st_size > 100:
            continue
        url = BASE.format(sid=sid)
        try:
            http_get(url, dest, ua="curl/8.0")
            head = dest.read_text(encoding="utf-8", errors="replace").splitlines()[0]
            if sid not in head:
                raise RuntimeError(f"unexpected header: {head[:80]!r}")
            write_fetch_meta(dest, url)
            print(f"[L06] {sid} — {dest.stat().st_size:,} bytes")
        except Exception as e:  # noqa: BLE001
            print(f"[L06] FAIL {sid}: {e}", file=sys.stderr)
            failures.append(sid)
    if failures:
        print(f"[L06] failed series: {failures}", file=sys.stderr)
        return 1
    print(f"[L06] {len(APU_IDS)} APU series fetched to {DEST_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
