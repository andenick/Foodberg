#!/usr/bin/env python3
"""L05 — Fetch BLS CPI series from the BLS public API v1 (keyless).

Source (public, keyless):
    https://api.bls.gov/publicAPI/v1/timeseries/data/   (POST, JSON)

Covers the NSA CUUR food series the site uses for its US composite. Two of
them (CUUR0000SEFV01/02) are NOT mirrored on FRED, which is why this loader
exists alongside L04.

Keyless limits: 25 series per query and a 10-year span per query — so the
fetch is windowed (start year configurable, default 1997 = the full life of
the SEFV01/02 series; 4 windows, 4 queries). Values are the publisher's own;
annual averages (period M13) are skipped.

Output: data/raw/bls/<SERIES_ID>.json (+ .fetch_meta.json)
        one merged {"series_id": {"name":..., "data":[{date,value}...]}} file
        at data/raw/bls/bls_series.json
"""

import json
import sys
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import RAW, write_fetch_meta  # noqa: E402

API = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
DEST_DIR = RAW / "bls"

BLS_IDS = [
    "CUUR0000SAF", "CUUR0000SAF11", "CUUR0000SAF111", "CUUR0000SAF112",
    "CUUR0000SAF113", "CUUR0000SEFJ", "CUUR0000SEFV",
    "CUUR0000SEFV01", "CUUR0000SEFV02",
]
DEFAULT_START = 1997  # full life of CUUR0000SEFV01/02 (Dec 1997=100 base)


def post_json(payload: dict) -> dict:
    import urllib.request
    req = urllib.request.Request(
        API, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "User-Agent": "FoodbergReplication/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def fetch_window(series_ids: list, y0: int, y1: int) -> dict:
    resp = post_json({"seriesid": series_ids,
                      "startyear": str(y0), "endyear": str(y1)})
    if resp.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError(f"BLS API error: {resp.get('message')}")
    out: dict = {}
    for s in resp["Results"]["series"]:
        out.setdefault(s["seriesID"], []).extend(s["data"])
    return out


def main() -> int:
    start = int(sys.argv[sys.argv.index("--start") + 1]) if "--start" in sys.argv else DEFAULT_START
    end = dt.date.today().year
    merged: dict = {}
    for y0 in range(start, end + 1, 10):
        y1 = min(y0 + 9, end)
        print(f"[L05] window {y0}-{y1} …")
        window = fetch_window(BLS_IDS, y0, y1)
        for sid, obs in window.items():
            merged.setdefault(sid, []).extend(obs)

    DEST_DIR.mkdir(parents=True, exist_ok=True)
    for sid in BLS_IDS:
        obs = merged.get(sid, [])
        # keep monthly periods only (M13 = annual average), newest last
        rows = []
        for o in obs:
            period = o.get("period", "")
            if not (period.startswith("M") and period[1:].isdigit()):
                continue
            month = int(period[1:])
            if not 1 <= month <= 12:
                continue
            rows.append({"date": f"{o['year']}-{month:02d}-01",
                         "value": o.get("value")})
        rows = [r for r in rows if r["value"] not in (None, "", "-", "NA")]
        rows.sort(key=lambda r: r["date"])
        seen, dedup = set(), []
        for r in rows:
            if r["date"] in seen:
                continue
            seen.add(r["date"])
            dedup.append(r)
        (DEST_DIR / f"{sid}.json").write_text(
            json.dumps({"series_id": sid, "data": dedup}, indent=1), encoding="utf-8")
        write_fetch_meta(DEST_DIR / f"{sid}.json", API)
        print(f"[L05] {sid}: {len(dedup)} observations")
        if not dedup:
            print(f"[L05] WARNING: no observations for {sid}", file=sys.stderr)

    missing = [s for s in BLS_IDS if s not in merged]
    if missing:
        print(f"[L05] FAIL: BLS returned nothing for {missing}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
