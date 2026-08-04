#!/usr/bin/env python3
"""
Foodberg — ingest four cheap, high-value MONTHLY BLS series (2026-07-24).

Adds, using the SAME keyless retrieval method already in production:

  economic_indicators
    WPU01130217      PPI, Farm Products: Tomatoes (index 1982=100, NSA).
                     Pairs with the retail APU0000712311 tomato series to give
                     the wholesale <-> retail wedge.               category PPI
    CUUR0000SEFV01   CPI, Full service meals and snacks (Dec 1997=100, NSA).
    CUUR0000SEFV02   CPI, Limited service meals and snacks.    category Food CPI

  retail_prices  (source 'BLS AP')
    APU0100712311    Tomatoes, field grown - Northeast Census Region - Urban
    APU0200712311    Tomatoes, field grown - Midwest   Census Region - Urban
    APU0300712311    Tomatoes, field grown - South     Census Region - Urban
    APU0400712311    Tomatoes, field grown - West      Census Region - Urban
                     (published nothing since 2025-03 - see LIVENESS below)

RETRIEVAL — no API key anywhere
-------------------------------
  * FRED keyless CSV mirror, identical to
    the store's BLS collector module (ap_via_fred_collector.py):
        https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES>
    Used for the four AP series and for WPU01130217.
  * BLS public API v1 (keyless, 25 queries/day, 10 years per query):
        https://api.bls.gov/publicAPI/v1/timeseries/data/
    Used ONLY for CUUR0000SEFV01/02, which FRED does not mirror (both 404 on
    fredgraph.csv, verified 2026-07-24). No key is required or sent.

NO FABRICATED OR PLACEHOLDER VALUES
-----------------------------------
  * FRED renders a BLS '-' placeholder / suppressed month as '.', which is
    dropped (never carried forward, never interpolated). Every live regional
    tomato series has a genuine hole at 2025-10 (the 2025 lapse in
    appropriations); that hole is preserved as an absence.
  * BLS API observations are kept only when the value parses as a float and the
    period is M01-M12 (M13 is an annual average, not a monthly observation).
    Any footnote text encountered is recorded in the artifact for audit.

LIVENESS
--------
Classified ONLY from the last real observation, by the single existing
classifier `WorldBankClient._liveness` (backend/data_sources/worldbank_client.py),
measured against the newest observation in the series' own source catalog. No
second classifier, no hardcoded discontinued flag, no publisher end_year.

OUTPUTS
-------
  <store>/DATA/BLS_AP/ap_fred_APU0[1-4]00712311.json   (store canonical)
  backend/data/collected/fred_food_extra.json                (source 'FRED')
  backend/data/collected/bls_food_extra.json                 (source 'BLS')
  backend/data/foodberg.db                                   (incremental load)

CONCURRENCY
-----------
The database is shared with other writers. This script uses
PRAGMA busy_timeout=60000, short per-series transactions, and inserts ONLY rows
that are not already present. It NEVER deletes and never VACUUMs, so it is safe
to run while another agent writes a different table. A full
`backend/database/rebake_history.py` run reproduces the same state.

USAGE
-----
    python Technical/scripts/ingest_bls_monthly_series.py            # fetch+load
    python Technical/scripts/ingest_bls_monthly_series.py --fetch-only
    python Technical/scripts/ingest_bls_monthly_series.py --load-only
    python Technical/scripts/ingest_bls_monthly_series.py --verify
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT = Path(__file__).resolve().parent.parent.parent
BACKEND = PROJECT / "backend"
DB_PATH = BACKEND / "data" / "foodberg.db"
COLLECTED = BACKEND / "data" / "collected"

# The single liveness classifier. Reused, never re-implemented.
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
from data_sources.worldbank_client import WorldBankClient  # noqa: E402

# Robin's canonical BLS AP store (same resolution rule as rebake_history.py).
_robin_env = os.environ.get("ROBIN_DATA_PATH", "").strip()
ROBIN = Path(_robin_env) if _robin_env else (
    PROJECT.parent.parent / "Council" / "Robin" / "DATA")
BLS_AP_DIR = ROBIN / "BLS_AP"

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
FRED_SERIES_PAGE = "https://fred.stlouisfed.org/series/{sid}"
BLS_API_V1 = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
BLS_SERIES_PAGE = "https://data.bls.gov/timeseries/{sid}"
UA = {"User-Agent": "ArcanumResearch/1.0"}

NOW = datetime.datetime.now()
NOW_ISO = NOW.isoformat()
NOW_SQL = NOW.isoformat(sep=" ", timespec="seconds")

LICENCE_USGOV = "U.S. Government work (public domain)"


# ---------------------------------------------------------------------------
# Series definitions
# ---------------------------------------------------------------------------

# BLS AP area codes 0100/0200/0300/0400 are the four Census regions. The
# `series_title` values are the publisher's own titles, verified 2026-07-24
# against the FRED series pages for APU0[1-4]00712311.
AP_REGIONAL: Dict[str, Dict[str, str]] = {
    "APU0100712311": {
        "region": "Northeast",
        "area_code": "0100",
        "area": "Northeast Census Region - Urban",
    },
    "APU0200712311": {
        "region": "Midwest",
        "area_code": "0200",
        "area": "Midwest Census Region - Urban",
    },
    "APU0300712311": {
        "region": "South",
        "area_code": "0300",
        "area": "South Census Region - Urban",
    },
    "APU0400712311": {
        "region": "West",
        "area_code": "0400",
        "area": "West Census Region - Urban",
    },
}
AP_ITEM_CODE = "712311"
AP_ITEM_BASE = "Tomatoes, field grown"          # BLS item 712311, as in Robin
AP_UNIT = "$ per lb"
AP_TITLE_TMPL = ("Average Price: Tomatoes, Field Grown (Cost per Pound/453.6 "
                 "Grams) in the {area}")

# economic_indicators series. `source` is the label written to the DB and must
# name the endpoint the data actually came from - it is what reality_audit.py
# resolves a retrieval URL from.
FRED_INDICATORS: Dict[str, Dict[str, str]] = {
    "WPU01130217": {
        "name": "PPI - Farm Products: Tomatoes",
        "series_title": ("Producer Price Index by Commodity: Farm Products: "
                         "Tomatoes"),
        "unit": "index 1982=100",
        "geography": "United States",
        "publisher": "U.S. Bureau of Labor Statistics",
        "revision_policy": (
            "PPI indexes are PRELIMINARY and subject to monthly revision for "
            "up to four months after original publication (BLS footnote, seen "
            "on 2026-03 and 2026-06). The monthly re-run upserts on "
            "(series_id, date, source), so revisions are picked up in place."),
        "coverage_note": (
            "BLS itself publishes no observation for several recent months "
            "(2026-01, -02, -04, -05 as of 2026-07-24) - verified against the "
            "BLS public API, so these are genuine publisher gaps, not losses "
            "in the FRED mirror. They are stored as absences."),
    },
}
BLS_INDICATORS: Dict[str, Dict[str, str]] = {
    "CUUR0000SEFV01": {
        "name": "CPI - Full Service Meals and Snacks",
        "series_title": ("Consumer Price Index for All Urban Consumers: Full "
                         "service meals and snacks in U.S. city average"),
        "unit": "index Dec 1997=100",
        "geography": "U.S. city average",
        "publisher": "U.S. Bureau of Labor Statistics",
        "coverage_note": (
            "2025-10 is published by BLS as the placeholder '-' footnoted "
            "'Data unavailable due to the 2025 lapse in appropriations'. It is "
            "dropped, not stored and not carried forward."),
    },
    "CUUR0000SEFV02": {
        "name": "CPI - Limited Service Meals and Snacks",
        "series_title": ("Consumer Price Index for All Urban Consumers: "
                         "Limited service meals and snacks in U.S. city "
                         "average"),
        "unit": "index Dec 1997=100",
        "geography": "U.S. city average",
        "publisher": "U.S. Bureau of Labor Statistics",
        "coverage_note": (
            "2025-10 is published by BLS as the placeholder '-' footnoted "
            "'Data unavailable due to the 2025 lapse in appropriations'. It is "
            "dropped, not stored and not carried forward."),
    },
}
# BLS public API v1 allows a 10-year span per query. These windows cover the
# full published history (both series begin 1997-12).
BLS_WINDOWS: List[Tuple[int, int]] = [(1997, 2006), (2007, 2016), (2017, 2026)]

FRED_EXTRA_PATH = COLLECTED / "fred_food_extra.json"
BLS_EXTRA_PATH = COLLECTED / "bls_food_extra.json"


def log(msg: str) -> None:
    print(f"[bls-monthly] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_fred_csv(sid: str) -> List[Dict[str, Any]]:
    """Keyless FRED CSV mirror. '.' and empty cells are DROPPED, never filled."""
    req = urllib.request.Request(FRED_CSV.format(sid=sid), headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        text = r.read().decode("utf-8")
    out: List[Dict[str, Any]] = []
    dropped = 0
    for line in text.strip().splitlines()[1:]:
        date_s, _, val_s = line.partition(",")
        val_s = val_s.strip()
        if not val_s or val_s == ".":
            dropped += 1
            continue
        try:
            out.append({"date": date_s.strip(), "value": float(val_s)})
        except ValueError:
            dropped += 1
    log(f"  {sid}: {len(out)} real observations "
        f"({dropped} missing/placeholder cells dropped, never filled)")
    return out


def fetch_bls_v1(sids: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Keyless BLS public API v1. Returns {sid: {'data': [...], 'footnotes': [...]}}.

    Only M01-M12 observations with a parseable float value are kept. M13 is the
    annual average and is not a monthly observation. Any footnote text seen is
    returned so a suppressed/placeholder print can never pass silently.
    """
    collected: Dict[str, Dict[str, Any]] = {
        s: {"obs": {}, "footnotes": {}, "dropped": 0} for s in sids}
    for y0, y1 in BLS_WINDOWS:
        payload = json.dumps({"seriesid": sids,
                              "startyear": str(y0), "endyear": str(y1)}).encode()
        req = urllib.request.Request(
            BLS_API_V1, data=payload,
            headers={"Content-Type": "application/json", **UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            body = json.loads(r.read().decode("utf-8"))
        status = body.get("status")
        if status != "REQUEST_SUCCEEDED":
            raise RuntimeError(
                f"BLS API v1 {y0}-{y1} returned {status}: {body.get('message')}")
        for block in body.get("Results", {}).get("series", []):
            sid = block["seriesID"]
            bucket = collected[sid]
            for obs in block.get("data", []):
                period = obs.get("period", "")
                if not (period.startswith("M") and period != "M13"):
                    continue
                try:
                    value = float(str(obs.get("value", "")).replace(",", ""))
                except ValueError:
                    bucket["dropped"] += 1
                    continue
                date = f"{obs['year']}-{int(period[1:]):02d}-01"
                bucket["obs"][date] = value
                for fn in obs.get("footnotes", []) or []:
                    text = (fn or {}).get("text")
                    if text:
                        bucket["footnotes"].setdefault(text, []).append(date)
        time.sleep(1.0)

    out: Dict[str, Dict[str, Any]] = {}
    for sid, bucket in collected.items():
        rows = [{"date": d, "value": v} for d, v in sorted(bucket["obs"].items())]
        out[sid] = {"data": rows, "footnotes": bucket["footnotes"]}
        log(f"  {sid}: {len(rows)} real observations "
            f"({bucket['dropped']} non-numeric values dropped)")
        for text, dates in bucket["footnotes"].items():
            log(f"    FOOTNOTE ({len(dates)} obs): {text[:120]}")
    return out


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------

def _ap_catalog_end() -> Optional[str]:
    """Newest real observation across Robin's whole BLS AP store."""
    end = None
    for path in sorted(BLS_AP_DIR.glob("ap_fred_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows = payload.get("data") or []
        if rows and (end is None or rows[-1]["date"] > end):
            end = rows[-1]["date"]
    return end


def _liveness(series_end: Optional[str], catalog_end: Optional[str]
              ) -> Dict[str, Any]:
    verdict = dict(WorldBankClient._liveness(series_end, catalog_end))
    verdict["catalog_end"] = catalog_end
    verdict["classifier"] = ("backend/data_sources/worldbank_client.py"
                             "::WorldBankClient._liveness")
    verdict["thresholds_months"] = {
        "stale": WorldBankClient.LIVENESS_STALE_MONTHS,
        "discontinued": WorldBankClient.LIVENESS_DISCONTINUED_MONTHS,
    }
    verdict["computed_at"] = NOW_ISO
    verdict["basis"] = ("last real observation vs newest observation in the "
                        "series' own source catalog; no end_year, no item-list "
                        "membership, no hardcoded flag")
    return verdict


def write_ap_artifacts(fetched: Dict[str, List[Dict[str, Any]]]) -> List[Path]:
    """Write Robin ap_fred_*.json files in the established shape, extended."""
    BLS_AP_DIR.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    # Catalog end must account for the series being written now.
    catalog_end = _ap_catalog_end()
    for rows in fetched.values():
        if rows and (catalog_end is None or rows[-1]["date"] > catalog_end):
            catalog_end = rows[-1]["date"]

    for sid, meta in AP_REGIONAL.items():
        rows = fetched[sid]
        if not rows:
            raise RuntimeError(f"{sid}: no real observations - refusing to write")
        item_name = f"{AP_ITEM_BASE} ({meta['region']})"
        title = AP_TITLE_TMPL.format(area=meta["area"])
        payload = {
            "series_id": sid,
            "item_code": AP_ITEM_CODE,
            "area_code": meta["area_code"],
            "item_name": item_name,
            "series_title": title,
            "unit": AP_UNIT,
            "area": meta["area"],
            "region": meta["region"],
            "source": "BLS Average Price (via FRED mirror)",
            "license": LICENCE_USGOV,
            "retrieved_at": NOW_ISO,
            "n_obs": len(rows),
            "date_range": {"start": rows[0]["date"], "end": rows[-1]["date"]},
            "provenance": {
                "source": "BLS Average Price (via FRED mirror)",
                "publisher": "U.S. Bureau of Labor Statistics",
                "publisher_series_id": sid,
                "publisher_series_title": title,
                "retrieval_url": FRED_CSV.format(sid=sid),
                "retrieval_method": "keyless FRED CSV mirror (no API key)",
                "publisher_landing": BLS_SERIES_PAGE.format(sid=sid),
                "fred_series_page": FRED_SERIES_PAGE.format(sid=sid),
                "retrieved_at": NOW_ISO,
                "unit": AP_UNIT,
                "geography": meta["area"],
                "license": LICENCE_USGOV,
                "frequency": "monthly",
                "placeholder_policy": (
                    "FRED '.' cells are dropped; no value is carried forward "
                    "or interpolated. Verified 2026-07-24 against the BLS "
                    "public API: 2025-10 is published by BLS as the "
                    "placeholder '-' footnoted 'Data unavailable due to the "
                    "2025 lapse in appropriations' for every one of these four "
                    "series, and for APU0400712311 that placeholder is the "
                    "ONLY entry after 2025-03. It is not stored."),
            },
            "liveness": _liveness(rows[-1]["date"], catalog_end),
            "data": rows,
        }
        out = BLS_AP_DIR / f"ap_fred_{sid}.json"
        out.write_text(json.dumps(payload), encoding="utf-8")
        written.append(out)
        lv = payload["liveness"]
        log(f"  wrote {out.name}: {len(rows)} obs "
            f"{rows[0]['date']}..{rows[-1]['date']} "
            f"liveness={lv['status']} ({lv['months_behind']} months behind "
            f"{lv['catalog_end']})")
    return written


def _indicator_block(sid: str, meta: Dict[str, str], rows: List[Dict[str, Any]],
                     source: str, retrieval_url: str, retrieval_method: str,
                     catalog_end: Optional[str],
                     footnotes: Optional[Dict[str, Any]] = None
                     ) -> Dict[str, Any]:
    """
    One economic_indicators series in the shape rebake_history.py already loads
    from backend/data/collected/*.json: {name, data[{series_id,date,value}],
    count}. Extra keys are carried for provenance and ignored by the loader.
    """
    return {
        "name": meta["name"],
        "data": [{"series_id": sid, "date": r["date"], "value": r["value"]}
                 for r in rows],
        "count": len(rows),
        "provenance": {
            "source": source,
            "publisher": meta["publisher"],
            "publisher_series_id": sid,
            "publisher_series_title": meta["series_title"],
            "retrieval_url": retrieval_url,
            "retrieval_method": retrieval_method,
            "publisher_landing": BLS_SERIES_PAGE.format(sid=sid),
            "retrieved_at": NOW_ISO,
            "unit": meta["unit"],
            "geography": meta["geography"],
            "license": LICENCE_USGOV,
            "frequency": "monthly",
            "placeholder_policy": (
                "only real published observations are stored; missing, "
                "suppressed and non-numeric prints are dropped, never filled"),
            **{k: meta[k] for k in ("revision_policy", "coverage_note")
               if k in meta},
        },
        "liveness": _liveness(rows[-1]["date"] if rows else None, catalog_end),
        "footnotes_seen": footnotes or {},
    }


def write_indicator_artifacts(fred_rows: Dict[str, List[Dict[str, Any]]],
                              bls_rows: Dict[str, Dict[str, Any]]) -> None:
    COLLECTED.mkdir(parents=True, exist_ok=True)

    fred_payload: Dict[str, Any] = {}
    for sid, meta in FRED_INDICATORS.items():
        rows = fred_rows[sid]
        if not rows:
            raise RuntimeError(f"{sid}: no real observations - refusing to write")
        fred_payload[sid] = _indicator_block(
            sid, meta, rows, "FRED", FRED_CSV.format(sid=sid),
            "keyless FRED CSV mirror (no API key)", rows[-1]["date"])
    FRED_EXTRA_PATH.write_text(json.dumps(fred_payload, indent=1),
                               encoding="utf-8")
    log(f"  wrote {FRED_EXTRA_PATH.name}: {len(fred_payload)} series")

    bls_payload: Dict[str, Any] = {}
    catalog_end = max((b["data"][-1]["date"] for b in bls_rows.values()
                       if b["data"]), default=None)
    for sid, meta in BLS_INDICATORS.items():
        block = bls_rows[sid]
        if not block["data"]:
            raise RuntimeError(f"{sid}: no real observations - refusing to write")
        bls_payload[sid] = _indicator_block(
            sid, meta, block["data"], "BLS", BLS_API_V1,
            "keyless BLS public API v1 (no registration key sent)",
            catalog_end, block["footnotes"])
    BLS_EXTRA_PATH.write_text(json.dumps(bls_payload, indent=1), encoding="utf-8")
    log(f"  wrote {BLS_EXTRA_PATH.name}: {len(bls_payload)} series")


# ---------------------------------------------------------------------------
# Incremental database load (concurrency-safe)
# ---------------------------------------------------------------------------

def connect() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB_PATH), timeout=60.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=60000")
    return con


def load_retail(con: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    """
    Insert regional AP observations into retail_prices, skipping any row already
    present. No DELETE: the 47 national BLS AP items are never touched.
    """
    stats: Dict[str, Dict[str, Any]] = {}
    ins = ("INSERT INTO retail_prices (food_item, price, unit, store_type, "
           "location, state, country, date, source, brand, quality_grade, "
           "imported_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)")
    for sid in AP_REGIONAL:
        payload = json.loads(
            (BLS_AP_DIR / f"ap_fred_{sid}.json").read_text(encoding="utf-8"))
        item, area = payload["item_name"], payload["area"]
        existing = {r["date"] for r in con.execute(
            "SELECT date FROM retail_prices WHERE source='BLS AP' "
            "AND food_item = ? AND location = ?", (item, area))}
        rows = [(item, r["value"], payload["unit"], "Grocery (avg)", area,
                 "", "USA", f"{r['date']} 00:00:00.000000", "BLS AP", "", "",
                 NOW_SQL)
                for r in payload["data"]
                if f"{r['date']} 00:00:00.000000" not in existing]
        con.execute("BEGIN IMMEDIATE")
        try:
            con.executemany(ins, rows)
            con.commit()
        except Exception:
            con.rollback()
            raise
        stats[sid] = {"food_item": item, "location": area,
                      "inserted": len(rows), "already_present": len(existing)}
        log(f"  retail_prices {sid} ({item}): +{len(rows)} rows "
            f"({len(existing)} already present)")
    return stats


def load_indicators(con: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    """Upsert on (series_id, date, source) - the rebake's own contract."""
    from importlib import import_module
    sys.path.insert(0, str(BACKEND / "database"))
    categorise = import_module("rebake_history")._indicator_category

    stats: Dict[str, Dict[str, Any]] = {}
    for path, source in ((FRED_EXTRA_PATH, "FRED"), (BLS_EXTRA_PATH, "BLS")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for sid, block in payload.items():
            category = categorise(sid)
            inserted = updated = 0
            con.execute("BEGIN IMMEDIATE")
            try:
                for obs in block["data"]:
                    date_full = f"{obs['date']} 00:00:00.000000"
                    hits = con.execute(
                        "SELECT id FROM economic_indicators WHERE series_id = ? "
                        "AND date = ? AND source = ?",
                        (sid, date_full, source)).fetchall()
                    if hits:
                        con.executemany(
                            "UPDATE economic_indicators SET value = ?, "
                            "imported_at = ? WHERE id = ?",
                            [(obs["value"], NOW_SQL, h["id"]) for h in hits])
                        updated += len(hits)
                    else:
                        con.execute(
                            "INSERT INTO economic_indicators (indicator_name, "
                            "series_id, value, date, category, frequency, "
                            "source, imported_at) VALUES (?,?,?,?,?,?,?,?)",
                            (block["name"], sid, obs["value"], date_full,
                             category, "Monthly", source, NOW_SQL))
                        inserted += 1
                con.commit()
            except Exception:
                con.rollback()
                raise
            stats[sid] = {"source": source, "category": category,
                          "inserted": inserted, "updated": updated}
            log(f"  economic_indicators {sid} [{source}/{category}]: "
                f"+{inserted} inserted, {updated} updated")
    return stats


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify(con: sqlite3.Connection) -> Dict[str, Any]:
    report: Dict[str, Any] = {"retail_prices": {}, "economic_indicators": {}}

    national = con.execute(
        "SELECT COUNT(*) n, COUNT(DISTINCT food_item) items FROM retail_prices "
        "WHERE source='BLS AP' AND location='U.S. city average'").fetchone()
    report["national_bls_ap_rows"] = national["n"]
    report["national_bls_ap_items"] = national["items"]
    log(f"national BLS AP (location='U.S. city average'): {national['n']:,} rows "
        f"across {national['items']} items")

    catalog_end = con.execute(
        "SELECT MAX(date) e FROM retail_prices WHERE source='BLS AP'"
    ).fetchone()["e"]
    for sid, meta in AP_REGIONAL.items():
        item = f"{AP_ITEM_BASE} ({meta['region']})"
        r = con.execute(
            "SELECT COUNT(*) n, MIN(date) d0, MAX(date) d1 FROM retail_prices "
            "WHERE source='BLS AP' AND food_item = ? AND location = ?",
            (item, meta["area"])).fetchone()
        lv = _liveness(str(r["d1"])[:10] if r["d1"] else None,
                       str(catalog_end)[:10] if catalog_end else None)
        report["retail_prices"][sid] = {
            "food_item": item, "location": meta["area"], "rows": r["n"],
            "first_observation": str(r["d0"])[:10] if r["d0"] else None,
            "last_real_observation": str(r["d1"])[:10] if r["d1"] else None,
            "liveness": lv,
        }
        log(f"  {sid} {item}: {r['n']} rows "
            f"{str(r['d0'])[:10]}..{str(r['d1'])[:10]} -> {lv['status']} "
            f"({lv['months_behind']} months behind catalog {lv['catalog_end']})")

    for sid in list(FRED_INDICATORS) + list(BLS_INDICATORS):
        r = con.execute(
            "SELECT source, category, COUNT(*) n, MIN(date) d0, MAX(date) d1 "
            "FROM economic_indicators WHERE series_id = ? GROUP BY source, "
            "category", (sid,)).fetchall()
        for row in r:
            end = con.execute(
                "SELECT MAX(date) e FROM economic_indicators WHERE source = ?",
                (row["source"],)).fetchone()["e"]
            lv = _liveness(str(row["d1"])[:10], str(end)[:10] if end else None)
            report["economic_indicators"][sid] = {
                "source": row["source"], "category": row["category"],
                "rows": row["n"],
                "first_observation": str(row["d0"])[:10],
                "last_real_observation": str(row["d1"])[:10],
                "liveness": lv,
            }
            log(f"  {sid} [{row['source']}/{row['category']}]: {row['n']} rows "
                f"{str(row['d0'])[:10]}..{str(row['d1'])[:10]} -> "
                f"{lv['status']} ({lv['months_behind']} months behind catalog "
                f"{lv['catalog_end']})")
    return report


# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--fetch-only", action="store_true",
                    help="write artifacts, do not touch the database")
    ap.add_argument("--load-only", action="store_true",
                    help="load existing artifacts, do not fetch")
    ap.add_argument("--verify", action="store_true",
                    help="report SQL counts and liveness only")
    args = ap.parse_args(argv)

    if args.verify:
        con = connect()
        try:
            print(json.dumps(verify(con), indent=2))
        finally:
            con.close()
        return 0

    if not args.load_only:
        log("FETCH — keyless FRED CSV mirror")
        ap_rows = {sid: fetch_fred_csv(sid) for sid in AP_REGIONAL}
        fred_rows = {sid: fetch_fred_csv(sid) for sid in FRED_INDICATORS}
        log("FETCH — keyless BLS public API v1 (FRED does not mirror SEFV01/02)")
        bls_rows = fetch_bls_v1(list(BLS_INDICATORS))
        log("WRITE artifacts")
        write_ap_artifacts(ap_rows)
        write_indicator_artifacts(fred_rows, bls_rows)

    if args.fetch_only:
        log("--fetch-only: database untouched")
        return 0

    if not DB_PATH.exists():
        print(f"database not found: {DB_PATH}", file=sys.stderr)
        return 2

    log("LOAD — incremental, no deletes, busy_timeout=60000")
    con = connect()
    try:
        load_retail(con)
        load_indicators(con)
        log("VERIFY")
        verify(con)
    finally:
        con.close()
    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
