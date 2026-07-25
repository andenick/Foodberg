#!/usr/bin/env python3
"""
Foodberg reality audit (P0-6).

Answers one question for every series the site can display: **is this real, and
is it what we say it is?**

For each series it emits a provenance record

    {source, publisher_series_id, retrieval_url, retrieved_at, unit,
     geography, last_real_observation, verdict}

and applies six checks. Anything the audit cannot establish is reported as the
literal string ``NOT CAPTURED`` - never guessed, never left blank in a way that
reads as "fine".

CHECKS
------
L  LIVENESS         Classify by the LAST REAL OBSERVATION, never by an
                    end_year or by membership in a publisher's item list.
                    Fifteen BLS AP items carry a 2025-M10 placeholder
                    ("data unavailable due to the 2025 lapse in
                    appropriations") whose real data is years older - sweet
                    peppers and broccoli stop at 2020-M03, chuck roast at
                    2017-M12. A series is judged against the newest
                    observation in its OWN source catalog, so the rule needs
                    no hardcoded "today" and cannot rot.
T  FLAT TAIL        A terminal run of identical values is how a placeholder
                    or a carried-forward value looks in a table that stores
                    no nulls. Reported as a warning for human eyes.
U  UNIT SANITY      Two failure modes. (a) A placeholder unit that carries no
                    information ('USD per unit', 'Value', 'various', ''). (b)
                    Series sharing one declared unit inside a source whose
                    magnitudes are incompatible - the five Alpha Vantage
                    series all declare 'USD per unit' while mixing cents/lb
                    (coffee ~321, cotton ~74) and $/mt (corn ~211, wheat ~175).
D  DUPLICATES       Repeated observations for one (series, date). 1,328
                    duplicate rows sit in global_prices' legacy World Bank
                    block.
N  NAME CLAIM       A recomputed series may never carry a publisher's name.
                    Either serve the published figure or rename it.
P  PROVENANCE       Every series must resolve to a publisher series ID (or
                    report slug) and a retrieval URL. Series that cannot are
                    quarantine candidates: do not display. USDA AMS wholesale
                    streams carry theirs per row (slug_name/slug_id,
                    retrieval_url, retrieved_at), written at ingest.

VERDICTS
--------
PASS  no flags, or informational flags only
WARN  displayable but must be labelled honestly (stale, discontinued,
      incomplete provenance, flat tail)
FAIL  must not be displayed as-is (placeholder unit, incompatible units under
      one label, duplicated observations, a recomputed series wearing a
      publisher's name)

USAGE
-----
    python Technical/scripts/reality_audit.py
    python Technical/scripts/reality_audit.py --gate     # exit 1 on any FAIL
    python Technical/scripts/reality_audit.py --db path/to/foodberg.db

Writes ``Technical/REALITY_AUDIT.json``. Intended to run on every rebake and
in CI, so a clean pass cannot silently regress.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB = PROJECT / "backend" / "data" / "foodberg.db"
DEFAULT_OUT = PROJECT / "Technical" / "REALITY_AUDIT.json"

NOT_CAPTURED = "NOT CAPTURED"

# Robin's canonical BLS Average Price store. Each ap_fred_*.json carries the
# publisher series id, unit, area, licence and retrieved_at - the only place
# in the pipeline where BLS AP provenance survives, because retail_prices has
# no series_id column.
_robin_env = os.environ.get("ROBIN_DATA_PATH", "").strip()
ROBIN = Path(_robin_env) if _robin_env else (
    PROJECT.parent.parent / "Council" / "Robin" / "DATA")
BLS_AP_DIR = ROBIN / "BLS_AP"


# --------------------------------------------------------------------------
# Source registry - publisher landing pages, verified public URLs.
# --------------------------------------------------------------------------

SOURCE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "BLS AP": {
        "publisher": "U.S. Bureau of Labor Statistics",
        "programme": "Average Price Data (AP)",
        "series_url_template": "https://data.bls.gov/timeseries/{series_id}",
        "landing": "https://www.bls.gov/cpi/data.htm",
        "licence": "U.S. Government work (public domain)",
        "frequency": "monthly",
    },
    "World Bank Pink Sheet": {
        "publisher": "World Bank",
        "programme": "Commodity Markets 'Pink Sheet' (Monthly)",
        "series_url_template": None,
        "landing": "https://www.worldbank.org/en/research/commodity-markets",
        "licence": "CC BY 4.0",
        "frequency": "monthly",
    },
    "FAO": {
        "publisher": "Food and Agriculture Organization of the United Nations",
        "programme": "FAO Food Price Index",
        "series_url_template": None,
        "landing": "https://www.fao.org/worldfoodsituation/foodpricesindex/en/",
        "licence": "CC BY 4.0",
        "frequency": "monthly",
    },
    "FAOSTAT": {
        "publisher": "FAO",
        "programme": "FAOSTAT Producer Prices (PP)",
        "series_url_template": None,
        "landing": "https://www.fao.org/faostat/en/#data/PP",
        "licence": "CC BY 4.0",
        "frequency": "annual",
    },
    "FAOSTAT CPI": {
        "publisher": "FAO",
        "programme": "FAOSTAT Consumer Price Indices (CP)",
        "series_url_template": None,
        "landing": "https://www.fao.org/faostat/en/#data/CP",
        "licence": "CC BY 4.0",
        "frequency": "monthly",
    },
    "World Bank": {
        "publisher": "World Bank",
        "programme": "World Development Indicators (legacy import)",
        "series_url_template": None,
        "landing": "https://data.worldbank.org/",
        "licence": "CC BY 4.0",
        "frequency": "annual",
    },
    "Alpha Vantage": {
        "publisher": "Alpha Vantage (commercial aggregator)",
        "programme": "Commodities API",
        "series_url_template": None,
        "landing": "https://www.alphavantage.co/documentation/#commodities",
        "licence": "UNRESOLVED - redistribution terms not established",
        "frequency": "monthly",
    },
    "FRED": {
        "publisher": "Federal Reserve Bank of St. Louis",
        "programme": "FRED",
        "series_url_template": "https://fred.stlouisfed.org/series/{series_id}",
        "landing": "https://fred.stlouisfed.org/",
        "licence": "mixed - underlying publisher terms apply",
        "frequency": "monthly",
    },
    "BLS": {
        "publisher": "U.S. Bureau of Labor Statistics",
        "programme": "CPI / PPI",
        "series_url_template": "https://data.bls.gov/timeseries/{series_id}",
        "landing": "https://www.bls.gov/data/",
        "licence": "U.S. Government work (public domain)",
        "frequency": "monthly",
    },
    "USDA NASS": {
        "publisher": "USDA National Agricultural Statistics Service",
        "programme": "Quick Stats - PRICE RECEIVED",
        "series_url_template": None,
        "landing": "https://quickstats.nass.usda.gov/",
        "licence": "U.S. Government work (public domain)",
        "frequency": "annual/monthly",
    },
    "USDA AMS Market News": {
        "publisher": "USDA Agricultural Marketing Service",
        "programme": "Market News - terminal market fruit & vegetable prices "
                     "(MARS API v3.1)",
        "series_url_template": None,
        "landing": "https://marsapi.ams.usda.gov/services/v3.1/reports",
        "licence": "U.S. Government work (public domain)",
        "frequency": "daily (business days)",
    },
    "Foodberg": {
        "publisher": "Foodberg (this site)",
        "programme": "derived composite",
        "series_url_template": None,
        "landing": None,
        "licence": "MIT (code) / underlying source terms (data)",
        "frequency": "monthly",
    },
}

# Units that name no actual unit. A series carrying one of these cannot be
# plotted honestly - the Price Explorer's y-axis literally reads "Value".
PLACEHOLDER_UNITS = {
    "", "value", "unit", "units", "various", "usd per unit", "n/a", "na",
    "none", "null", "-",
}

# Publisher tokens that a category name must not claim unless the series
# carries that publisher's published numbers.
PUBLISHER_TOKENS = {
    "fao": "FAO",
    "faostat": "FAO",
    "bls": "U.S. Bureau of Labor Statistics",
    "usda": "USDA",
    "nass": "USDA NASS",
    "wb": "World Bank",
    "worldbank": "World Bank",
    "oecd": "OECD",
    "imf": "IMF",
}

LIVENESS_STALE_MONTHS = 6
LIVENESS_DISCONTINUED_MONTHS = 24
FLAT_TAIL_MIN_RUN = 6
# Two series sharing one declared unit whose typical magnitudes differ by more
# than this factor cannot both be in that unit.
UNIT_MAGNITUDE_RATIO = 8.0


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def parse_ym(value: Any) -> Optional[Tuple[int, int]]:
    """Parse 'YYYY-MM-DD…', 'YYYY-MM' or a bare 'YYYY' into (year, month)."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        year = int(s[:4])
    except ValueError:
        return None
    if len(s) >= 7 and s[4] == "-":
        try:
            return year, int(s[5:7])
        except ValueError:
            return None
    return year, 12


def months_between(earlier: Any, later: Any) -> Optional[int]:
    a, b = parse_ym(earlier), parse_ym(later)
    if a is None or b is None:
        return None
    return (b[0] - a[0]) * 12 + (b[1] - a[1])


def iso_day(value: Any) -> str:
    if value is None:
        return NOT_CAPTURED
    return str(value)[:10]


class Series:
    """One auditable series plus the flags raised against it."""

    def __init__(self, key: str, table: str, source: str, name: str):
        self.key = key
        self.table = table
        self.source = source
        self.name = name
        self.publisher_series_id: Any = NOT_CAPTURED
        self.retrieval_url: Any = NOT_CAPTURED
        self.retrieved_at: Any = NOT_CAPTURED
        self.unit: Any = NOT_CAPTURED
        self.geography: Any = NOT_CAPTURED
        self.frequency: Any = NOT_CAPTURED
        self.licence: Any = NOT_CAPTURED
        self.first_observation: Any = NOT_CAPTURED
        self.last_real_observation: Any = NOT_CAPTURED
        self.n_observations = 0
        self.median_abs_value: Optional[float] = None
        self.flags: List[Dict[str, str]] = []
        self.notes: List[str] = []

    def flag(self, code: str, severity: str, detail: str) -> None:
        self.flags.append({"code": code, "severity": severity, "detail": detail})

    @property
    def verdict(self) -> str:
        severities = {f["severity"] for f in self.flags}
        if "FAIL" in severities:
            return "FAIL"
        if "WARN" in severities:
            return "WARN"
        return "PASS"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "series_key": self.key,
            "name": self.name,
            "table": self.table,
            "source": self.source,
            "publisher": SOURCE_REGISTRY.get(self.source, {}).get(
                "publisher", NOT_CAPTURED),
            "publisher_series_id": self.publisher_series_id,
            "retrieval_url": self.retrieval_url,
            "retrieved_at": self.retrieved_at,
            "unit": self.unit,
            "geography": self.geography,
            "frequency": self.frequency,
            "licence": self.licence,
            "first_observation": self.first_observation,
            "last_real_observation": self.last_real_observation,
            "n_observations": self.n_observations,
            "verdict": self.verdict,
            "flags": self.flags,
            "notes": self.notes,
        }


# --------------------------------------------------------------------------
# Provenance sidecar: Robin's BLS AP store
# --------------------------------------------------------------------------

def load_bls_ap_provenance() -> Dict[str, Dict[str, Any]]:
    """Map BLS AP item_name -> full provenance record from Robin's store."""
    out: Dict[str, Dict[str, Any]] = {}
    if not BLS_AP_DIR.is_dir():
        return out
    for path in sorted(BLS_AP_DIR.glob("ap_fred_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        item = payload.get("item_name")
        if item:
            out[item] = payload
    return out


# --------------------------------------------------------------------------
# Series collection, one table at a time
# --------------------------------------------------------------------------

def collect_retail_prices(con: sqlite3.Connection) -> List[Series]:
    prov = load_bls_ap_provenance()
    series: List[Series] = []
    rows = con.execute(
        "SELECT food_item, source, MIN(unit) unit, MIN(location) loc, "
        "COUNT(*) n, MIN(date) d0, MAX(date) d1 "
        "FROM retail_prices GROUP BY food_item, source").fetchall()
    for r in rows:
        s = Series(f"retail_prices::{r['source']}::{r['food_item']}",
                   "retail_prices", r["source"], r["food_item"])
        s.unit = r["unit"] or NOT_CAPTURED
        s.geography = r["loc"] or NOT_CAPTURED
        s.n_observations = r["n"]
        s.first_observation = iso_day(r["d0"])
        s.last_real_observation = iso_day(r["d1"])
        s.frequency = SOURCE_REGISTRY.get(r["source"], {}).get(
            "frequency", NOT_CAPTURED)
        s.licence = SOURCE_REGISTRY.get(r["source"], {}).get(
            "licence", NOT_CAPTURED)

        p = prov.get(r["food_item"])
        if p:
            s.publisher_series_id = p.get("series_id", NOT_CAPTURED)
            s.retrieved_at = p.get("retrieved_at", NOT_CAPTURED)
            s.licence = p.get("license", s.licence)
            s.unit = p.get("unit", s.unit)
            s.geography = p.get("area", s.geography)
            tpl = SOURCE_REGISTRY.get(r["source"], {}).get("series_url_template")
            if tpl and s.publisher_series_id != NOT_CAPTURED:
                s.retrieval_url = tpl.format(series_id=s.publisher_series_id)
        series.append(s)
    return series


def collect_global_prices(con: sqlite3.Connection) -> List[Series]:
    series: List[Series] = []
    rows = con.execute(
        "SELECT source, commodity, MIN(unit) unit, MIN(indicator_code) code, "
        "COUNT(*) n, COUNT(DISTINCT country) n_country, "
        "MIN(region) region, MIN(date) d0, MAX(date) d1 "
        "FROM global_prices GROUP BY source, commodity").fetchall()
    for r in rows:
        s = Series(f"global_prices::{r['source']}::{r['commodity']}",
                   "global_prices", r["source"], r["commodity"])
        reg = SOURCE_REGISTRY.get(r["source"], {})
        s.unit = r["unit"] or NOT_CAPTURED
        s.n_observations = r["n"]
        s.first_observation = iso_day(r["d0"])
        s.last_real_observation = iso_day(r["d1"])
        s.frequency = reg.get("frequency", NOT_CAPTURED)
        s.licence = reg.get("licence", NOT_CAPTURED)
        s.retrieval_url = reg.get("landing") or NOT_CAPTURED
        s.publisher_series_id = r["code"] or NOT_CAPTURED

        if r["n_country"] and r["n_country"] > 1:
            s.geography = f"{r['n_country']} countries"
        elif r["region"]:
            s.geography = r["region"]
        else:
            s.geography = NOT_CAPTURED
        series.append(s)
    return series


def collect_economic_indicators(con: sqlite3.Connection) -> List[Series]:
    series: List[Series] = []
    rows = con.execute(
        "SELECT source, series_id, MIN(indicator_name) name, "
        "COUNT(*) n, MIN(date) d0, MAX(date) d1, MAX(imported_at) imported "
        "FROM economic_indicators GROUP BY source, series_id").fetchall()
    for r in rows:
        s = Series(f"economic_indicators::{r['source']}::{r['series_id']}",
                   "economic_indicators", r["source"],
                   r["name"] or r["series_id"])
        reg = SOURCE_REGISTRY.get(r["source"], {})
        s.publisher_series_id = r["series_id"]
        s.n_observations = r["n"]
        s.first_observation = iso_day(r["d0"])
        s.last_real_observation = iso_day(r["d1"])
        s.retrieved_at = str(r["imported"]) if r["imported"] else NOT_CAPTURED
        s.frequency = reg.get("frequency", NOT_CAPTURED)
        s.licence = reg.get("licence", NOT_CAPTURED)
        s.geography = "United States"
        # economic_indicators has no unit column - index series are unitless
        # index points, but that is an assumption, not a captured fact.
        s.unit = NOT_CAPTURED
        s.notes.append(
            "economic_indicators has no unit column; unit is not captured "
            "anywhere in the pipeline for this table.")
        tpl = reg.get("series_url_template")
        if tpl:
            s.retrieval_url = tpl.format(series_id=r["series_id"])
        series.append(s)
    return series


def collect_composite_indices(con: sqlite3.Connection) -> List[Series]:
    series: List[Series] = []
    rows = con.execute(
        "SELECT category, COUNT(*) n, MIN(date) d0, MAX(date) d1, "
        "MIN(base_period) base, MAX(computed_at) computed "
        "FROM composite_indices GROUP BY category").fetchall()
    for r in rows:
        cat = r["category"]
        sample = con.execute(
            "SELECT components_json FROM composite_indices "
            "WHERE category = ? ORDER BY date DESC LIMIT 1", (cat,)).fetchone()
        meta: Dict[str, Any] = {}
        if sample and sample["components_json"]:
            try:
                parsed = json.loads(sample["components_json"])
                if isinstance(parsed, dict):
                    meta = parsed
            except json.JSONDecodeError:
                pass

        declared_publisher = meta.get("publisher")
        kind = meta.get("series")           # 'published' | 'recomputed' | None
        source = declared_publisher or "Foodberg"

        s = Series(f"composite_indices::{cat}", "composite_indices", source, cat)
        s.n_observations = r["n"]
        s.first_observation = iso_day(r["d0"])
        s.last_real_observation = iso_day(r["d1"])
        s.retrieved_at = str(r["computed"]) if r["computed"] else NOT_CAPTURED
        s.unit = f"index ({r['base']}=100)" if r["base"] else NOT_CAPTURED
        s.geography = "World" if cat.startswith("fao") or "global" in cat else "United States"
        s.frequency = "monthly"
        reg = SOURCE_REGISTRY.get(source, {})
        s.licence = reg.get("licence", NOT_CAPTURED)
        s.retrieval_url = reg.get("landing") or NOT_CAPTURED
        s.publisher_series_id = meta.get("publisher_series", NOT_CAPTURED)
        s.notes.append(f"derivation={kind or NOT_CAPTURED}")

        # A Foodberg-derived series has no publisher to fetch it from. Its
        # traceable provenance is the code that computes it plus the declared
        # method - not an external URL. Record that rather than reporting a
        # false "NOT CAPTURED", which would drown the real provenance gaps.
        if kind == "recomputed" and s.publisher_series_id == NOT_CAPTURED:
            s.publisher_series_id = f"foodberg:{cat}"
            s.retrieval_url = (
                "derived in backend/indices/composite.py — not published by "
                "any external source")
            method = meta.get("method")
            if method:
                s.notes.append(f"method={method}")
            if meta.get("weights"):
                s.notes.append(f"weights={json.dumps(meta['weights'])}")
            else:
                s.notes.append(
                    "weights NOT CAPTURED in components_json — the derivation "
                    "cannot be reproduced from the database alone.")
        # Stash for the NAME CLAIM check.
        s._composite_kind = kind            # type: ignore[attr-defined]
        s._composite_meta = meta            # type: ignore[attr-defined]
        series.append(s)
    return series


def collect_nass_price_series(con: sqlite3.Connection) -> List[Series]:
    """USDA NASS PRICE RECEIVED, national - what the Price Explorer browses."""
    series: List[Series] = []
    rows = con.execute(
        "SELECT commodity, MIN(unit) unit, COUNT(*) n, "
        "COUNT(DISTINCT year) ny, MIN(year) y0, MAX(year) y1 "
        "FROM wasde_data WHERE statistic_category='PRICE RECEIVED' "
        "AND agg_level='NATIONAL' AND numeric_value IS NOT NULL "
        "GROUP BY commodity").fetchall()
    reg = SOURCE_REGISTRY["USDA NASS"]
    for r in rows:
        s = Series(f"wasde_data::USDA NASS::{r['commodity']}",
                   "wasde_data", "USDA NASS", str(r["commodity"]))
        s.unit = r["unit"] or NOT_CAPTURED
        s.n_observations = r["n"]
        s.first_observation = str(r["y0"])
        s.last_real_observation = str(r["y1"])
        s.geography = "United States"
        s.frequency = reg["frequency"]
        s.licence = reg["licence"]
        s.retrieval_url = reg["landing"]
        series.append(s)
    return series


def collect_ams_wholesale_prices(con: sqlite3.Connection) -> List[Series]:
    """USDA AMS daily terminal-market wholesale prices.

    One auditable series per PUBLISHED REPORT STREAM, because the report slug
    is the publisher's own series identity: slug_name NX_FV020 / slug_id 2315
    is 'New York Terminal Market Vegetables Prices'. Provenance is read from
    the rows themselves - retrieval_url and retrieved_at are stored per row by
    the ingest, so nothing here is asserted on the data's behalf.

    The unit is deliberately expressed against the quoted PACKAGE. AMS prices
    a specific package of a specific lot ('16 kg cartons', '50 lb sacks'), and
    a stream carries many packages at once; collapsing that to one number
    would be the dishonest move, so the package stays a column and the unit
    says so.
    """
    exists = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        ("ams_wholesale_prices",)).fetchone()
    if not exists:
        return []

    series: List[Series] = []
    rows = con.execute(
        "SELECT slug_name, MIN(slug_id) slug_id, MIN(report_title) title, "
        "       MIN(geography) geo, COUNT(*) n, "
        "       COUNT(DISTINCT package) n_pack, MIN(package) one_pack, "
        "       COUNT(DISTINCT commodity) n_comm, "
        "       MIN(report_date) d0, MAX(report_date) d1, "
        "       MAX(retrieved_at) got, MIN(retrieval_url) url, MIN(source) src "
        "FROM ams_wholesale_prices GROUP BY slug_name").fetchall()

    for r in rows:
        source = r["src"] or "USDA AMS Market News"
        reg = SOURCE_REGISTRY.get(source, {})
        s = Series(f"ams_wholesale_prices::{source}::{r['slug_name']}",
                   "ams_wholesale_prices", source,
                   r["title"] or str(r["slug_name"]))
        s.publisher_series_id = (
            f"{r['slug_name']} (slug_id {r['slug_id']})"
            if r["slug_id"] else r["slug_name"])
        s.retrieval_url = r["url"] or NOT_CAPTURED
        s.retrieved_at = r["got"] or NOT_CAPTURED
        if r["n_pack"] == 1 and r["one_pack"]:
            s.unit = f"USD per {r['one_pack']}"
        elif r["n_pack"]:
            s.unit = (f"USD per quoted package ({r['n_pack']} distinct packages "
                      f"in this report; see the package column)")
        s.geography = r["geo"] or NOT_CAPTURED
        s.frequency = reg.get("frequency", NOT_CAPTURED)
        s.licence = reg.get("licence", NOT_CAPTURED)
        s.n_observations = r["n"]
        s.first_observation = iso_day(r["d0"])
        s.last_real_observation = iso_day(r["d1"])
        s.notes.append(
            f"{r['n_comm']} distinct commodities; price is quoted for the "
            f"package, so package/variety/grade/origin are preserved per row "
            f"and never collapsed to a single price.")
        series.append(s)
    return series


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def check_liveness(series: List[Series]) -> None:
    """L: classify by LAST REAL OBSERVATION, per source catalog."""
    newest: Dict[str, Any] = {}
    for s in series:
        if s.last_real_observation == NOT_CAPTURED:
            continue
        cur = newest.get(s.source)
        if cur is None or str(s.last_real_observation) > str(cur):
            newest[s.source] = s.last_real_observation

    for s in series:
        catalog_end = newest.get(s.source)
        if s.last_real_observation == NOT_CAPTURED or catalog_end is None:
            s.flag("L_LIVENESS_UNKNOWN", "WARN",
                   "No last real observation could be established.")
            continue
        behind = months_between(s.last_real_observation, catalog_end)
        if behind is None:
            s.flag("L_LIVENESS_UNKNOWN", "WARN",
                   f"Unparseable observation date {s.last_real_observation!r}.")
        elif behind >= LIVENESS_DISCONTINUED_MONTHS:
            s.flag("L_DISCONTINUED", "WARN",
                   f"Last real observation {s.last_real_observation} is "
                   f"{behind} months behind the newest observation in the "
                   f"{s.source} catalog ({catalog_end}). Must not be presented "
                   f"as current; label as discontinued.")
        elif behind >= LIVENESS_STALE_MONTHS:
            s.flag("L_STALE", "WARN",
                   f"Last real observation {s.last_real_observation} is "
                   f"{behind} months behind the {s.source} catalog "
                   f"({catalog_end}). Needs a staleness marker.")


def check_flat_tail(con: sqlite3.Connection, series: List[Series]) -> None:
    """T: a terminal run of identical values smells like a placeholder."""
    for s in series:
        if s.table == "retail_prices":
            sql = ("SELECT price v FROM retail_prices WHERE food_item=? "
                   "AND source=? ORDER BY date DESC LIMIT 24")
            args = (s.name, s.source)
        elif s.table == "global_prices":
            sql = ("SELECT price v FROM global_prices WHERE commodity=? "
                   "AND source=? ORDER BY date DESC LIMIT 24")
            args = (s.name, s.source)
        elif s.table == "composite_indices":
            sql = ("SELECT index_value v FROM composite_indices "
                   "WHERE category=? ORDER BY date DESC LIMIT 24")
            args = (s.name,)
        else:
            continue

        try:
            values = [r["v"] for r in con.execute(sql, args).fetchall()]
        except sqlite3.Error:
            continue
        if len(values) < FLAT_TAIL_MIN_RUN:
            continue
        run = 1
        for a, b in zip(values, values[1:]):
            if a == b:
                run += 1
            else:
                break
        if run >= FLAT_TAIL_MIN_RUN:
            s.flag("T_FLAT_TAIL", "WARN",
                   f"The last {run} observations are all {values[0]!r}. "
                   f"Verify these are real prints, not a carried-forward or "
                   f"placeholder value.")


def is_placeholder_unit(unit: Any) -> bool:
    """True when a unit is present but names nothing (not merely absent)."""
    if unit == NOT_CAPTURED or unit is None:
        return False          # absent -> a provenance problem, not a wrong label
    return str(unit).strip().lower() in PLACEHOLDER_UNITS


def check_units(series: List[Series]) -> None:
    """U(a): a declared unit that names no actual unit."""
    for s in series:
        if is_placeholder_unit(s.unit):
            s.flag("U_UNIT_PLACEHOLDER", "FAIL",
                   f"Declared unit {s.unit!r} names no actual unit. A chart "
                   f"axis cannot be labelled honestly from it.")


def _median_abs(con: sqlite3.Connection, s: Series) -> Optional[float]:
    if s.table == "retail_prices":
        sql = ("SELECT price v FROM retail_prices WHERE food_item=? "
               "AND source=?")
        args: Tuple[Any, ...] = (s.name, s.source)
    elif s.table == "global_prices":
        sql = "SELECT price v FROM global_prices WHERE commodity=? AND source=?"
        args = (s.name, s.source)
    elif s.table == "composite_indices":
        sql = "SELECT index_value v FROM composite_indices WHERE category=?"
        args = (s.name,)
    else:
        return None
    try:
        vals = [abs(r["v"]) for r in con.execute(sql, args).fetchall()
                if r["v"] is not None]
    except sqlite3.Error:
        return None
    return statistics.median(vals) if vals else None


def check_unit_magnitudes(con: sqlite3.Connection, series: List[Series]) -> None:
    """
    U(b): corroborating evidence that a placeholder unit is hiding a real unit
    mismatch.

    Deliberately scoped to groups whose declared unit is ALREADY a placeholder.
    Wide magnitude dispersion under a *real* unit is normal and is not a
    defect: 212 FAOSTAT commodities legitimately share 'USD/tonne' while
    spanning saffron to wheat, and 41 BLS AP items legitimately share '$ per
    lb'. Firing on those would bury the genuine finding - the five Alpha
    Vantage series that declare 'USD per unit' while mixing cents/lb
    (coffee, cotton) with $/mt (corn, wheat).

    Severity is WARN: the FAIL for these series already comes from
    U_UNIT_PLACEHOLDER. This flag exists to prove the placeholder is
    load-bearing rather than merely sloppy.
    """
    groups: Dict[Tuple[str, str], List[Series]] = defaultdict(list)
    for s in series:
        if not is_placeholder_unit(s.unit):
            continue
        groups[(s.source, str(s.unit))].append(s)

    for (source, unit), members in groups.items():
        if len(members) < 2:
            continue
        medians: List[Tuple[Series, float]] = []
        for s in members:
            m = _median_abs(con, s)
            if m and m > 0:
                s.median_abs_value = m
                medians.append((s, m))
        if len(medians) < 2:
            continue
        lo_s, lo = min(medians, key=lambda t: t[1])
        hi_s, hi = max(medians, key=lambda t: t[1])
        if hi / lo > UNIT_MAGNITUDE_RATIO:
            detail = (
                f"{len(medians)} series in source {source!r} all declare unit "
                f"{unit!r}, but typical magnitudes span {lo:.4g} "
                f"({lo_s.name}) to {hi:.4g} ({hi_s.name}) - a factor of "
                f"{hi / lo:.0f}. They cannot all be in that unit.")
            for s, _ in medians:
                s.flag("U_UNIT_INCONSISTENT", "WARN", detail)


def check_duplicates(con: sqlite3.Connection, series: List[Series]) -> Dict[str, Any]:
    """D: repeated observations for one (series, date)."""
    by_key = {s.key: s for s in series}
    summary: Dict[str, Any] = {"global_prices": {}, "retail_prices": {},
                               "composite_indices": {}, "economic_indicators": {}}

    rows = con.execute(
        "SELECT source, commodity, SUM(k - 1) excess, COUNT(*) groups FROM ("
        "  SELECT source, commodity, date, country, region, COUNT(*) k "
        "  FROM global_prices GROUP BY 1,2,3,4,5 HAVING k > 1"
        ") GROUP BY source, commodity").fetchall()
    total_excess = 0
    for r in rows:
        total_excess += r["excess"]
        key = f"global_prices::{r['source']}::{r['commodity']}"
        summary["global_prices"][key] = {
            "duplicate_groups": r["groups"], "excess_rows": r["excess"]}
        s = by_key.get(key)
        if s:
            s.flag("D_DUPLICATE_OBSERVATIONS", "FAIL",
                   f"{r['excess']} duplicate observation rows across "
                   f"{r['groups']} (date, country, region) groups. Any "
                   f"aggregate over this series double-counts.")
    summary["global_prices_total_excess_rows"] = total_excess

    rows = con.execute(
        "SELECT source, food_item, SUM(k - 1) excess, COUNT(*) groups FROM ("
        "  SELECT source, food_item, date, location, COUNT(*) k "
        "  FROM retail_prices GROUP BY 1,2,3,4 HAVING k > 1"
        ") GROUP BY source, food_item").fetchall()
    for r in rows:
        key = f"retail_prices::{r['source']}::{r['food_item']}"
        summary["retail_prices"][key] = {
            "duplicate_groups": r["groups"], "excess_rows": r["excess"]}
        s = by_key.get(key)
        if s:
            s.flag("D_DUPLICATE_OBSERVATIONS", "FAIL",
                   f"{r['excess']} duplicate observation rows.")

    rows = con.execute(
        "SELECT category, SUM(k - 1) excess FROM ("
        "  SELECT category, date, COUNT(*) k FROM composite_indices "
        "  GROUP BY 1,2 HAVING k > 1) GROUP BY category").fetchall()
    for r in rows:
        key = f"composite_indices::{r['category']}"
        summary["composite_indices"][key] = {"excess_rows": r["excess"]}
        s = by_key.get(key)
        if s:
            s.flag("D_DUPLICATE_OBSERVATIONS", "FAIL",
                   f"{r['excess']} duplicate observation rows.")

    rows = con.execute(
        "SELECT source, series_id, SUM(k - 1) excess FROM ("
        "  SELECT source, series_id, date, COUNT(*) k FROM economic_indicators "
        "  GROUP BY 1,2,3 HAVING k > 1) GROUP BY source, series_id").fetchall()
    for r in rows:
        key = f"economic_indicators::{r['source']}::{r['series_id']}"
        summary["economic_indicators"][key] = {"excess_rows": r["excess"]}
        s = by_key.get(key)
        if s:
            s.flag("D_DUPLICATE_OBSERVATIONS", "FAIL",
                   f"{r['excess']} duplicate observation rows.")

    return summary


def check_name_claims(series: List[Series]) -> None:
    """N: a recomputed series may never carry a publisher's name."""
    for s in series:
        kind = getattr(s, "_composite_kind", None)
        if s.table != "composite_indices":
            continue
        tokens = [t for t in str(s.name).replace("-", "_").split("_") if t]
        claimed = next((PUBLISHER_TOKENS[t] for t in tokens
                        if t.lower() in PUBLISHER_TOKENS), None)
        if not claimed:
            continue
        if kind == "published":
            continue
        if kind == "recomputed":
            s.flag("N_PUBLISHER_NAME_ON_RECOMPUTED_SERIES", "FAIL",
                   f"Category {s.name!r} claims {claimed}, but the series is "
                   f"RECOMPUTED by Foodberg. Serve the published figure under "
                   f"that name, or rename the series.")
        else:
            s.flag("N_DERIVATION_UNDECLARED", "FAIL",
                   f"Category {s.name!r} claims {claimed} but does not declare "
                   f"whether it is published or recomputed. Cannot be shown "
                   f"under a publisher's name until it does.")


def check_provenance(series: List[Series]) -> None:
    """P: every series must resolve to an ID (or slug) and a retrieval URL."""
    for s in series:
        missing = [label for label, value in (
            ("publisher_series_id", s.publisher_series_id),
            ("retrieval_url", s.retrieval_url),
            ("retrieved_at", s.retrieved_at),
            ("unit", s.unit),
            ("geography", s.geography),
        ) if value == NOT_CAPTURED]
        if not missing:
            continue
        hard = "retrieval_url" in missing
        s.flag("P_PROVENANCE_INCOMPLETE", "FAIL" if hard else "WARN",
               "Not captured: " + ", ".join(missing) +
               (". No retrieval URL means the value cannot be traced to a "
                "publisher; quarantine candidate."
                if hard else ". Displayable, but provenance is thin."))


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def run_audit(db_path: Path) -> Dict[str, Any]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        series: List[Series] = []
        series += collect_retail_prices(con)
        series += collect_global_prices(con)
        series += collect_economic_indicators(con)
        series += collect_composite_indices(con)
        series += collect_nass_price_series(con)
        series += collect_ams_wholesale_prices(con)

        check_liveness(series)
        check_flat_tail(con, series)
        check_units(series)
        check_unit_magnitudes(con, series)
        duplicates = check_duplicates(con, series)
        check_name_claims(series)
        check_provenance(series)
    finally:
        con.close()

    by_verdict = defaultdict(int)
    by_flag = defaultdict(int)
    for s in series:
        by_verdict[s.verdict] += 1
        for f in s.flags:
            by_flag[f["code"]] += 1

    fails = sorted((s for s in series if s.verdict == "FAIL"),
                   key=lambda s: s.key)

    return {
        "audit": "Foodberg reality audit",
        "spec": "FOODBERG_CHEF_FIRST_PLAN_20260724.md P0-6",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": str(db_path),
        "thresholds": {
            "liveness_stale_months": LIVENESS_STALE_MONTHS,
            "liveness_discontinued_months": LIVENESS_DISCONTINUED_MONTHS,
            "flat_tail_min_run": FLAT_TAIL_MIN_RUN,
            "unit_magnitude_ratio": UNIT_MAGNITUDE_RATIO,
        },
        "summary": {
            "series_audited": len(series),
            "verdicts": dict(by_verdict),
            "flags": dict(sorted(by_flag.items())),
            "failing_series": [s.key for s in fails],
        },
        "duplicates": duplicates,
        "series": [s.to_dict() for s in sorted(series, key=lambda s: s.key)],
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Foodberg reality audit (P0-6)")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 if any series verdict is FAIL")
    args = ap.parse_args(argv)

    if not args.db.exists():
        print(f"database not found: {args.db}", file=sys.stderr)
        return 2

    report = run_audit(args.db)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    s = report["summary"]
    print(f"Foodberg reality audit -> {args.out}")
    print(f"  series audited : {s['series_audited']}")
    for verdict in ("PASS", "WARN", "FAIL"):
        print(f"  {verdict:5}          : {s['verdicts'].get(verdict, 0)}")
    print("  flags raised:")
    for code, n in s["flags"].items():
        print(f"    {code:42} {n}")
    if s["failing_series"]:
        print(f"  FAILING SERIES ({len(s['failing_series'])}):")
        for key in s["failing_series"][:40]:
            print(f"    {key}")
        if len(s["failing_series"]) > 40:
            print(f"    … and {len(s['failing_series']) - 40} more")

    if args.gate and s["verdicts"].get("FAIL"):
        print("\nGATE FAILED: at least one series must not be displayed as-is.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
