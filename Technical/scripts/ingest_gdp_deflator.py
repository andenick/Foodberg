#!/usr/bin/env python3
"""
Foodberg — ingest the GDP implicit price deflator (GDPDEF) (2026-07-25).

Adds, using the SAME keyless retrieval method already in production:

  economic_indicators
    GDPDEF           GDP Implicit Price Deflator (index 2017=100, SA, quarterly).
                     Published by the U.S. Bureau of Economic Analysis in the
                     NIPA accounts (Table 1.1.9) and mirrored by FRED.
                     category 'Deflator', frequency 'Quarterly', source 'FRED'.

WHY A DEFLATOR AND WHY NOT CPI
------------------------------
`Council/Carson/Technical/standards/WEBSITE_VISUALIZATION_STANDARD.md` §2
requires that a nominal series which benefits from it be offered in REAL terms
using the **GDP deflator**, and it forbids using the CPI for that adjustment.
The CPI is a fixed-basket consumer-price measure whose own basket contains the
very food prices Foodberg charts, so deflating a food price by the CPI would
partly deflate food by food. The GDP deflator is an economy-wide implicit
price index derived from the full national accounts and is the standard
whole-economy price level for converting nominal dollars to real dollars.

  ** NEVER USE CPI FOR REAL-TERMS ADJUSTMENT ON THIS SITE. **

This script therefore ingests GDPDEF and nothing else. The CPI series already
in `economic_indicators` (CUUR*/CPIAUCSL) stay what they are — published price
indexes shown in their own right — and must not be used as a deflator.

RETRIEVAL — no API key anywhere
-------------------------------
  * FRED keyless CSV mirror, identical to the method in
    Technical/scripts/ingest_bls_monthly_series.py and
    Council/Robin/API_MODULES/BLS/ap_via_fred_collector.py:
        https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPDEF
    Verified 2026-07-25: HTTP 200, columns `observation_date,GDPDEF`,
    quarterly, 1947-01-01 -> 2026-01-01.

NO FABRICATED OR PLACEHOLDER VALUES
-----------------------------------
  * FRED renders a missing/suppressed quarter as '.', which is DROPPED — never
    carried forward, never interpolated. A quarterly observation is stored on
    the first day of its quarter, exactly as the publisher dates it; it is NOT
    expanded to three monthly rows. Monthly-to-quarterly alignment is the
    consumer's job (the API serves the quarterly series as published).
  * The index base period is not asserted from memory: it is CHECKED against
    the data (the base year is the one whose four quarters average to 100.000)
    and the script fails loudly if that check does not land on the expected
    year.

IDEMPOTENCE
-----------
The load DELETEs every `economic_indicators` row with series_id='GDPDEF' and
re-inserts the fetched series in one transaction, so re-running the script is a
no-op in aggregate and can never accumulate duplicate observations (the
D_DUPLICATE_OBSERVATIONS class in Technical/scripts/reality_audit.py). No other
series_id is ever touched. `PRAGMA wal_checkpoint(TRUNCATE)` is run afterwards
so the WAL does not keep the change out of the baked file.

OUTPUTS
-------
  backend/data/collected/fred_gdp_deflator.json   (provenance artifact, source 'FRED')
  backend/data/foodberg.db                        (economic_indicators, GDPDEF)

Registered in backend/database/rebake_history.py::COLLECTED_SOURCES, so a full
rebake reproduces the same state from the same artifact.

USAGE
-----
    python Technical/scripts/ingest_gdp_deflator.py            # fetch+load
    python Technical/scripts/ingest_gdp_deflator.py --fetch-only
    python Technical/scripts/ingest_gdp_deflator.py --load-only
    python Technical/scripts/ingest_gdp_deflator.py --verify
"""

from __future__ import annotations

import argparse
import datetime
import json
import sqlite3
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT = Path(__file__).resolve().parent.parent.parent
BACKEND = PROJECT / "backend"
DB_PATH = BACKEND / "data" / "foodberg.db"
COLLECTED = BACKEND / "data" / "collected"

# The single liveness classifier. Reused, never re-implemented.
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
from data_sources.worldbank_client import WorldBankClient  # noqa: E402

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
FRED_SERIES_PAGE = "https://fred.stlouisfed.org/series/{sid}"
BEA_LANDING = ("https://apps.bea.gov/iTable/?reqid=19&step=2&isuri=1&"
               "categories=survey")
UA = {"User-Agent": "ArcanumResearch/1.0"}

NOW = datetime.datetime.now()
NOW_ISO = NOW.isoformat()
NOW_SQL = NOW.isoformat(sep=" ", timespec="seconds")

LICENCE_USGOV = "U.S. Government work (public domain)"

SERIES_ID = "GDPDEF"
INDICATOR_NAME = "GDP Implicit Price Deflator"
CATEGORY = "Deflator"
FREQUENCY = "Quarterly"
SOURCE = "FRED"

# The publisher's own metadata for the series, verified 2026-07-25 against
# https://fred.stlouisfed.org/series/GDPDEF.
META: Dict[str, Any] = {
    "name": INDICATOR_NAME,
    "series_title": "Gross Domestic Product: Implicit Price Deflator",
    "unit": "index 2017=100",
    "base_year": 2017,
    "seasonal_adjustment": "Seasonally adjusted",
    "geography": "United States",
    "publisher": "U.S. Bureau of Economic Analysis",
    "publisher_programme": ("National Income and Product Accounts, Table 1.1.9 "
                            "(Implicit Price Deflators for Gross Domestic "
                            "Product)"),
    "revision_policy": (
        "BEA revises the NIPA accounts monthly (advance/second/third GDP "
        "estimates) and annually, so recent quarters change. The load is a "
        "full delete-and-reinsert of this series_id, so revisions are picked "
        "up in place rather than accumulating."),
    "usage_note": (
        "Use ONLY this series to convert nominal prices to real (constant-"
        "dollar) prices on Foodberg. WEBSITE_VISUALIZATION_STANDARD §2 "
        "requires the GDP deflator and forbids the CPI for this purpose."),
}

ARTIFACT_PATH = COLLECTED / "fred_gdp_deflator.json"


def log(msg: str) -> None:
    print(f"[gdp-deflator] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_fred_csv(sid: str) -> List[Dict[str, Any]]:
    """Keyless FRED CSV mirror. '.' and empty cells are DROPPED, never filled."""
    url = FRED_CSV.format(sid=sid)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        text = r.read().decode("utf-8")
    lines = text.strip().splitlines()
    header = lines[0].strip() if lines else ""
    if sid not in header:
        raise RuntimeError(f"{sid}: unexpected CSV header {header!r}")
    out: List[Dict[str, Any]] = []
    dropped = 0
    for line in lines[1:]:
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


# ---------------------------------------------------------------------------
# Checks on the fetched series (no assertion is taken from memory)
# ---------------------------------------------------------------------------

def check_base_year(rows: List[Dict[str, Any]], expected: int) -> Dict[str, Any]:
    """
    Establish the index base period FROM THE DATA: the base year of an index
    with base=100 is the year whose observations average to 100.

    Returns the evidence; raises if the data does not agree with `expected`,
    because a silently rebased deflator would silently corrupt every real-terms
    chart on the site.
    """
    by_year: Dict[int, List[float]] = {}
    for r in rows:
        by_year.setdefault(int(r["date"][:4]), []).append(r["value"])
    means = {y: sum(v) / len(v) for y, v in by_year.items() if len(v) == 4}
    if not means:
        raise RuntimeError("no complete year in the fetched series")
    base = min(means, key=lambda y: abs(means[y] - 100.0))
    evidence = {
        "base_year_detected": base,
        "mean_of_base_year": round(means[base], 6),
        "n_quarters_in_base_year": len(by_year[base]),
        "method": ("the year whose four quarterly observations average to "
                   "100.000; computed from the fetched data, not asserted"),
    }
    if base != expected or abs(means[base] - 100.0) > 0.05:
        raise RuntimeError(
            f"base-period check failed: expected {expected}=100, found "
            f"{base}={means[base]:.4f}. FRED may have rebased GDPDEF; update "
            f"META['unit'] and META['base_year'] after verifying the series "
            f"page, and re-check every real-terms chart.")
    log(f"  base period verified from the data: {base}=100 "
        f"(mean of {base} = {means[base]:.4f})")
    return evidence


def check_quarterly(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Confirm the series really is quarterly (months 1/4/7/10, no gaps kept
    silent). Returns the evidence; never modifies the data."""
    months = sorted({int(r["date"][5:7]) for r in rows})
    if months != [1, 4, 7, 10]:
        raise RuntimeError(
            f"{SERIES_ID} is not quarterly as expected: observation months "
            f"{months}")
    gaps: List[str] = []
    prev = None
    for r in rows:
        y, m = int(r["date"][:4]), int(r["date"][5:7])
        cur = y * 4 + (m - 1) // 3
        if prev is not None and cur != prev + 1:
            gaps.append(r["date"])
        prev = cur
    log(f"  frequency verified from the data: quarterly, observation months "
        f"{months}, {len(gaps)} internal gaps")
    return {"observation_months": months, "internal_gaps": gaps,
            "method": "observation months and quarter-index continuity"}


# ---------------------------------------------------------------------------
# Artifact
# ---------------------------------------------------------------------------

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
    verdict["basis"] = ("last real observation vs the newest observation of "
                        "this series itself; GDPDEF is its own catalog (it is "
                        "the only deflator ingested), and a quarterly series is "
                        "at least one quarter behind the calendar by "
                        "construction")
    return verdict


def write_artifact(rows: List[Dict[str, Any]], checks: Dict[str, Any]) -> Path:
    """
    Write the collected artifact in the shape rebake_history.py already loads
    from backend/data/collected/*.json: {series_id: {name, data[{series_id,
    date, value}], count}}. Extra keys carry provenance; the loader ignores
    everything it does not know, except `frequency`, which it honours.
    """
    if not rows:
        raise RuntimeError(f"{SERIES_ID}: no real observations - refusing to write")
    COLLECTED.mkdir(parents=True, exist_ok=True)
    payload = {
        SERIES_ID: {
            "name": META["name"],
            "frequency": FREQUENCY,
            "category": CATEGORY,
            "data": [{"series_id": SERIES_ID, "date": r["date"],
                      "value": r["value"]} for r in rows],
            "count": len(rows),
            "provenance": {
                "source": SOURCE,
                "publisher": META["publisher"],
                "publisher_programme": META["publisher_programme"],
                "publisher_series_id": SERIES_ID,
                "publisher_series_title": META["series_title"],
                "retrieval_url": FRED_CSV.format(sid=SERIES_ID),
                "retrieval_method": "keyless FRED CSV mirror (no API key)",
                "publisher_landing": BEA_LANDING,
                "fred_series_page": FRED_SERIES_PAGE.format(sid=SERIES_ID),
                "retrieved_at": NOW_ISO,
                "unit": META["unit"],
                "base_period": META["unit"],
                "seasonal_adjustment": META["seasonal_adjustment"],
                "geography": META["geography"],
                "license": LICENCE_USGOV,
                "frequency": "quarterly",
                "placeholder_policy": (
                    "FRED '.' cells are dropped; no value is carried forward, "
                    "interpolated, or expanded from quarterly to monthly"),
                "revision_policy": META["revision_policy"],
                "usage_note": META["usage_note"],
            },
            "checks": checks,
            "liveness": _liveness(rows[-1]["date"], rows[-1]["date"]),
            "date_range": {"start": rows[0]["date"], "end": rows[-1]["date"]},
        }
    }
    ARTIFACT_PATH.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    log(f"  wrote {ARTIFACT_PATH.name}: {len(rows)} obs "
        f"{rows[0]['date']}..{rows[-1]['date']}")
    return ARTIFACT_PATH


# ---------------------------------------------------------------------------
# Database load (idempotent: delete this series_id, then insert)
# ---------------------------------------------------------------------------

def connect() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB_PATH), timeout=60.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=60000")
    return con


def load_indicator(con: sqlite3.Connection) -> Dict[str, Any]:
    """Delete every GDPDEF row, then insert the artifact's observations."""
    payload = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    block = payload[SERIES_ID]
    observations = block["data"]
    if not observations:
        raise RuntimeError(f"{SERIES_ID}: artifact has no observations")

    before = con.execute(
        "SELECT COUNT(*) n FROM economic_indicators WHERE series_id = ?",
        (SERIES_ID,)).fetchone()["n"]

    con.execute("BEGIN IMMEDIATE")
    try:
        con.execute("DELETE FROM economic_indicators WHERE series_id = ?",
                    (SERIES_ID,))
        con.executemany(
            "INSERT INTO economic_indicators (indicator_name, series_id, value, "
            "date, category, frequency, source, imported_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            [(block["name"], SERIES_ID, obs["value"],
              f"{obs['date']} 00:00:00.000000", CATEGORY, FREQUENCY, SOURCE,
              NOW_SQL) for obs in observations])
        con.commit()
    except Exception:
        con.rollback()
        raise

    log(f"  economic_indicators {SERIES_ID} [{SOURCE}/{CATEGORY}/{FREQUENCY}]: "
        f"deleted {before}, inserted {len(observations)}")
    return {"deleted": before, "inserted": len(observations)}


def checkpoint(con: sqlite3.Connection) -> Dict[str, Any]:
    """Fold the WAL back into the baked database file."""
    row = con.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    result = {"busy": row[0], "wal_pages": row[1], "checkpointed_pages": row[2]}
    log(f"  wal_checkpoint(TRUNCATE): busy={row[0]} wal_pages={row[1]} "
        f"checkpointed={row[2]}")
    return result


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify(con: sqlite3.Connection) -> Dict[str, Any]:
    r = con.execute(
        "SELECT COUNT(*) n, COUNT(DISTINCT date) dates, MIN(date) d0, "
        "MAX(date) d1, MIN(indicator_name) name, MIN(category) cat, "
        "MIN(frequency) freq, MIN(source) src "
        "FROM economic_indicators WHERE series_id = ?", (SERIES_ID,)).fetchone()
    if not r["n"]:
        log(f"{SERIES_ID}: NOT PRESENT in economic_indicators")
        return {"series_id": SERIES_ID, "rows": 0, "present": False}

    latest = con.execute(
        "SELECT date, value FROM economic_indicators WHERE series_id = ? "
        "ORDER BY date DESC LIMIT 1", (SERIES_ID,)).fetchone()
    dupes = r["n"] - r["dates"]
    lv = _liveness(str(r["d1"])[:10], str(r["d1"])[:10])
    report = {
        "series_id": SERIES_ID, "present": True, "rows": r["n"],
        "distinct_dates": r["dates"], "duplicate_rows": dupes,
        "indicator_name": r["name"], "category": r["cat"],
        "frequency": r["freq"], "source": r["src"],
        "first_observation": str(r["d0"])[:10],
        "last_real_observation": str(r["d1"])[:10],
        "latest": {"date": str(latest["date"])[:10], "value": latest["value"]},
        "liveness": lv,
        "retrieval_url": FRED_CSV.format(sid=SERIES_ID),
    }
    log(f"  {SERIES_ID} [{r['src']}/{r['cat']}/{r['freq']}]: {r['n']} rows "
        f"{str(r['d0'])[:10]}..{str(r['d1'])[:10]}, latest "
        f"{report['latest']['date']} = {report['latest']['value']}, "
        f"{dupes} duplicate rows")
    if dupes:
        raise RuntimeError(
            f"{SERIES_ID}: {dupes} duplicate (series_id, date) rows present - "
            f"the load is supposed to be a delete-and-reinsert")
    return report


# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Ingest FRED GDPDEF (GDP implicit price deflator) into "
                    "economic_indicators. GDP deflator, never CPI.")
    ap.add_argument("--fetch-only", action="store_true",
                    help="write the artifact, do not touch the database")
    ap.add_argument("--load-only", action="store_true",
                    help="load the existing artifact, do not fetch")
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
        rows = fetch_fred_csv(SERIES_ID)
        log("CHECK — base period and frequency, from the data")
        checks = {"base_period": check_base_year(rows, META["base_year"]),
                  "frequency": check_quarterly(rows)}
        log("WRITE artifact")
        write_artifact(rows, checks)

    if args.fetch_only:
        log("--fetch-only: database untouched")
        return 0

    if not DB_PATH.exists():
        print(f"database not found: {DB_PATH}", file=sys.stderr)
        return 2

    log("LOAD — idempotent (DELETE series_id then INSERT), busy_timeout=60000")
    con = connect()
    try:
        load_indicator(con)
        log("VERIFY")
        verify(con)
        log("CHECKPOINT")
        checkpoint(con)
    finally:
        con.close()
    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
