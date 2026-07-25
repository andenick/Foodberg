#!/usr/bin/env python3
"""Ingest USDA AMS Market News daily terminal-market wholesale prices.

Loads the MARS API v3.1 "Report Details" line items for every ACTIVE terminal
market into ``ams_wholesale_prices`` in ``backend/data/foodberg.db``, then
records the run in ``data_source_sync`` and refreshes the Carson cadence
registry — all in one run, so the registry can never drift from the data it
describes (the S8 staleness defect).

DESIGN NOTES
------------
* Markets come from the LIVE MARS CATALOG (see backend/data_sources/usda_client.py).
  Nothing about which cities exist, what they are called, or which are
  discontinued is hardcoded here.
* Idempotent: rows are written with INSERT OR IGNORE against a UNIQUE
  row_hash digest of the whole price line item, so re-running any window is a
  no-op while every genuinely distinct published line survives. (The obvious
  nine-column natural key is NOT unique in AMS's own data — see the note in
  backend/database/models.py.)
* Resumable: every completed (slug_id, window) is checkpointed to a JSON state
  file, so an interrupted load restarts where it stopped.
* Concurrency-safe: ``PRAGMA busy_timeout=60000`` and short batched
  transactions, because other processes write other tables in this database.
* Honest: a window that returns nothing stores nothing. No placeholder rows,
  no carried-forward prices, no invented dates.

USAGE
-----
    python Technical/scripts/ingest_ams.py --days 365
    python Technical/scripts/ingest_ams.py --start 01/01/2026 --end 07/24/2026
    python Technical/scripts/ingest_ams.py --days 5 --markets new_york,chicago
    python Technical/scripts/ingest_ams.py --full-history
    python Technical/scripts/ingest_ams.py --days 365 --restart   # ignore state

The API credential is read from the OS credential vault at runtime by
usda_client.load_api_key(). It is never written to disk or logged here.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

PROJECT = Path(__file__).resolve().parent.parent.parent
BACKEND = PROJECT / "backend"
DEFAULT_DB = BACKEND / "data" / "foodberg.db"
STATE_DIR = PROJECT / "Technical" / "state"
DEFAULT_STATE = STATE_DIR / "ams_ingest_state.json"
CADENCE_REGISTRY = (
    PROJECT.parent.parent
    / "Council" / "Carson" / "Technical" / "registries" / "data_cadence.json"
)

sys.path.insert(0, str(BACKEND))

from data_sources.usda_client import (  # noqa: E402
    PROGRAMME_LANDING,
    USDAMarketNewsClient,
    mmddyyyy_to_iso,
)

SOURCE_NAME = "USDA AMS Market News"
TABLE = "ams_wholesale_prices"

# Column order used by every INSERT in this script.
COLUMNS: Sequence[str] = (
    "report_date", "published_date", "slug_id", "slug_name", "report_title",
    "market", "city", "state", "geography",
    "category", "commodity", "variety", "package", "grade", "item_size",
    "organic", "origin", "origin_detail", "repack", "storage", "quality",
    "condition", "appearance", "crop", "district", "environment",
    "transportation_mode", "unit_of_sale",
    "low_price", "high_price", "mostly_low_price", "mostly_high_price",
    "market_tone_comments",
    "unit", "source", "retrieval_url", "retrieved_at", "row_hash",
)

# The digest that makes a re-run a no-op. Covers the identity of the price
# line AND its four prices, because AMS prints several genuinely distinct
# lines per lot description per day (see the note in database/models.py).
# It deliberately excludes report-level metadata (title, market tone,
# published_date) and the retrieval stamp, which are not part of the
# observation.
HASH_FIELDS: Sequence[str] = (
    "report_date", "slug_id", "commodity", "variety", "package", "grade",
    "item_size", "organic", "origin", "origin_detail", "repack", "storage",
    "quality", "condition", "appearance", "crop", "district", "environment",
    "transportation_mode", "unit_of_sale",
    "low_price", "high_price", "mostly_low_price", "mostly_high_price",
)


def row_hash(item: Dict[str, Any]) -> str:
    payload = "".join(
        "" if item.get(f) is None else str(item.get(f)) for f in HASH_FIELDS
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()

DDL = f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date TEXT NOT NULL,
    published_date TEXT,
    slug_id TEXT NOT NULL,
    slug_name TEXT NOT NULL,
    report_title TEXT,
    market TEXT,
    city TEXT,
    state TEXT,
    geography TEXT,
    category TEXT,
    commodity TEXT NOT NULL,
    variety TEXT,
    package TEXT,
    grade TEXT,
    item_size TEXT,
    organic TEXT,
    origin TEXT,
    origin_detail TEXT,
    repack TEXT,
    storage TEXT,
    quality TEXT,
    condition TEXT,
    appearance TEXT,
    crop TEXT,
    district TEXT,
    environment TEXT,
    transportation_mode TEXT,
    unit_of_sale TEXT,
    low_price REAL,
    high_price REAL,
    mostly_low_price REAL,
    mostly_high_price REAL,
    market_tone_comments TEXT,
    unit TEXT,
    source TEXT,
    retrieval_url TEXT,
    retrieved_at TEXT,
    row_hash TEXT NOT NULL
)
"""

# ux_ams_row_hash is the idempotence constraint; ix_ams_natural_key is the
# nine-column lookup path (non-unique, because AMS publishes several distinct
# price lines per lot description per day).
INDEX_DDL = (
    f"CREATE UNIQUE INDEX IF NOT EXISTS ux_ams_row_hash ON {TABLE} (row_hash)",
    f"CREATE INDEX IF NOT EXISTS ix_ams_natural_key ON {TABLE} ("
    "report_date, slug_id, commodity, variety, package, grade, item_size, "
    "organic, origin)",
    f"CREATE INDEX IF NOT EXISTS ix_ams_commodity_date ON {TABLE} (commodity, report_date)",
    f"CREATE INDEX IF NOT EXISTS ix_ams_market_date ON {TABLE} (market, report_date)",
    f"CREATE INDEX IF NOT EXISTS ix_ams_city_date ON {TABLE} (city, report_date)",
    f"CREATE INDEX IF NOT EXISTS ix_ams_report_date ON {TABLE} (report_date)",
)

INSERT_SQL = (
    f"INSERT OR IGNORE INTO {TABLE} ({', '.join(COLUMNS)}) "
    f"VALUES ({', '.join('?' * len(COLUMNS))})"
)


# ---------------------------------------------------------------------------
# database plumbing
# ---------------------------------------------------------------------------

def connect(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path), timeout=60.0, isolation_level=None)
    # Another process writes other tables in this database concurrently.
    con.execute("PRAGMA busy_timeout=60000")
    con.row_factory = sqlite3.Row
    return con


def ensure_schema(con: sqlite3.Connection) -> None:
    con.execute("BEGIN IMMEDIATE")
    try:
        con.execute(DDL)
        for stmt in INDEX_DDL:
            con.execute(stmt)
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise


def table_stats(con: sqlite3.Connection) -> Dict[str, Any]:
    row = con.execute(
        f"SELECT COUNT(*) n, COUNT(DISTINCT city) cities, "
        f"COUNT(DISTINCT commodity) commodities, COUNT(DISTINCT slug_name) slugs, "
        f"MIN(report_date) d0, MAX(report_date) d1 FROM {TABLE}"
    ).fetchone()
    # Read the stream inventory from the DATA, not from whatever subset of
    # markets this particular invocation happened to select.
    slug_rows = con.execute(
        f"SELECT DISTINCT slug_name, slug_id FROM {TABLE} ORDER BY slug_name"
    ).fetchall()
    return {
        "slugs": [f"{r['slug_name']}={r['slug_id']}" for r in slug_rows],
        "rows": row["n"],
        "cities": row["cities"],
        "commodities": row["commodities"],
        "report_streams": row["slugs"],
        "first_report_date": row["d0"],
        "last_report_date": row["d1"],
    }


# ---------------------------------------------------------------------------
# resumable state
# ---------------------------------------------------------------------------

def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"version": 1, "completed": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "completed": {}}
    data.setdefault("completed", {})
    return data


def save_state(path: Path, state: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


# ---------------------------------------------------------------------------
# windows
# ---------------------------------------------------------------------------

def month_windows(start: dt.date, end: dt.date) -> List[tuple]:
    """Split [start, end] into calendar-month windows (bounded responses)."""
    windows = []
    cursor = start
    while cursor <= end:
        if cursor.month == 12:
            next_month = dt.date(cursor.year + 1, 1, 1)
        else:
            next_month = dt.date(cursor.year, cursor.month + 1, 1)
        window_end = min(next_month - dt.timedelta(days=1), end)
        windows.append((cursor, window_end))
        cursor = window_end + dt.timedelta(days=1)
    return windows


def probe_history_floor(
    client: USDAMarketNewsClient,
    reference_slug_id: str,
    earliest_year: int = 1998,
) -> dt.date:
    """Find the earliest year the API still serves for a reference report.

    Probed on ONE representative stream rather than all 40+ (each probe is a
    live request). Windows that turn out to be empty for other streams simply
    store nothing — an over-wide start date costs requests, never bad data.
    """
    this_year = dt.date.today().year
    for year in range(earliest_year, this_year + 1):
        try:
            rows = client.fetch_report_details(
                reference_slug_id, dt.date(year, 1, 1), dt.date(year, 3, 31)
            )
        except Exception:  # noqa: BLE001 - a failed probe just means "try later"
            continue
        if rows:
            print(f"  history floor probe: data found from {year}")
            return dt.date(year, 1, 1)
    return dt.date(this_year, 1, 1)


# ---------------------------------------------------------------------------
# ingest
# ---------------------------------------------------------------------------

def rows_to_tuples(
    raw_rows: Iterable[Dict[str, Any]],
    stream: Dict[str, Any],
    retrieved_at: str,
) -> List[tuple]:
    out: List[tuple] = []
    for raw in raw_rows:
        item = USDAMarketNewsClient.normalize_detail_row(raw)
        # Two fields the publisher must supply for the row to be addressable.
        if not item["report_date"] or not item["commodity"]:
            continue
        item["slug_id"] = item["slug_id"] or stream["slug_id"]
        item["slug_name"] = item["slug_name"] or stream["slug_name"]
        item["market"] = item["market"] or stream["market"]
        item["city"] = item["city"] or stream["city"]
        item["state"] = item["state"] or stream["state"]
        item["geography"] = item["geography"] or ", ".join(
            p for p in (stream["city"], stream["state"]) if p
        ) or None
        item["source"] = SOURCE_NAME
        item["retrieval_url"] = stream["detail_url"]
        item["retrieved_at"] = retrieved_at
        item["row_hash"] = row_hash(item)
        out.append(tuple(item[c] for c in COLUMNS))
    return out


def ingest(
    con: sqlite3.Connection,
    client: USDAMarketNewsClient,
    streams: List[Dict[str, Any]],
    start: dt.date,
    end: dt.date,
    state: Dict[str, Any],
    state_path: Path,
    batch_rows: int = 5000,
) -> Dict[str, Any]:
    windows = month_windows(start, end)
    total_units = len(streams) * len(windows)
    print(
        f"ingest plan: {len(streams)} report streams x {len(windows)} monthly "
        f"windows = {total_units} requests  [{start} .. {end}]"
    )

    inserted = 0
    fetched = 0
    done = 0
    skipped = 0
    errors: List[str] = []
    pending: List[tuple] = []
    started = time.time()

    def flush() -> None:
        nonlocal pending, inserted
        if not pending:
            return
        con.execute("BEGIN IMMEDIATE")
        try:
            before = con.total_changes
            con.executemany(INSERT_SQL, pending)
            inserted += con.total_changes - before
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        pending = []

    for stream in streams:
        for w_start, w_end in windows:
            key = f"{stream['slug_id']}:{w_start.isoformat()}:{w_end.isoformat()}"
            done += 1
            if key in state["completed"]:
                skipped += 1
                continue
            try:
                raw = client.fetch_report_details(stream["slug_id"], w_start, w_end)
            except Exception as exc:  # noqa: BLE001
                msg = f"{stream['slug_name']} {w_start}..{w_end}: {type(exc).__name__}: {exc}"
                errors.append(msg)
                print(f"  ! {msg}")
                continue

            fetched += len(raw)
            pending.extend(rows_to_tuples(raw, stream, dt.datetime.now(dt.timezone.utc).isoformat()))
            state["completed"][key] = {"rows": len(raw), "at": dt.datetime.now(dt.timezone.utc).isoformat()}

            if len(pending) >= batch_rows:
                flush()
                save_state(state_path, state)

            if done % 25 == 0 or done == total_units:
                rate = done / max(time.time() - started, 1e-6)
                print(
                    f"  [{done}/{total_units}] {stream['slug_name']} "
                    f"{w_start:%Y-%m} | fetched {fetched:,} | inserted {inserted:,} "
                    f"| skipped {skipped} | {rate:.1f} req/s"
                )

    flush()
    save_state(state_path, state)

    return {
        "requests_planned": total_units,
        "requests_skipped_resumed": skipped,
        "line_items_fetched": fetched,
        "rows_inserted": inserted,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# sync ledger + cadence registry (written together with the ingest)
# ---------------------------------------------------------------------------

def record_sync(
    con: sqlite3.Connection, status: str, records: int, error: Optional[str],
    next_sync: Optional[str],
) -> None:
    now = dt.datetime.now().isoformat()
    con.execute("BEGIN IMMEDIATE")
    try:
        con.execute(
            "INSERT INTO data_source_sync "
            "(source_name, last_sync_time, last_sync_status, records_synced, "
            " error_message, next_sync_time, sync_frequency) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(source_name) DO UPDATE SET "
            "  last_sync_time=excluded.last_sync_time, "
            "  last_sync_status=excluded.last_sync_status, "
            "  records_synced=excluded.records_synced, "
            "  error_message=excluded.error_message, "
            "  next_sync_time=excluded.next_sync_time, "
            "  sync_frequency=excluded.sync_frequency",
            (SOURCE_NAME, now, status, records, error, next_sync, "daily"),
        )
        # The pre-rewrite integration logged its failure under the older label
        # 'USDA Market News' ("attempted relative import beyond top-level
        # package"). That row is the same source; leave it in place for
        # continuity but stop it reporting a failure that no longer exists.
        con.execute(
            "UPDATE data_source_sync SET last_sync_time=?, last_sync_status=?, "
            "records_synced=?, error_message=?, next_sync_time=?, sync_frequency=? "
            "WHERE source_name=? AND source_name<>?",
            (
                now, status, records,
                f"superseded by data_source_sync entry '{SOURCE_NAME}'",
                next_sync, "daily", "USDA Market News", SOURCE_NAME,
            ),
        )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise


def next_business_day(after: dt.date) -> dt.date:
    day = after + dt.timedelta(days=1)
    while day.weekday() >= 5:  # 5=Sat, 6=Sun
        day += dt.timedelta(days=1)
    return day


def update_cadence_registry(
    registry_path: Path, stats: Dict[str, Any],
) -> Optional[str]:
    """ADD/UPDATE the Foodberg AMS cadence entry. Other sites are untouched.

    Called in the same run as the ingest, from the numbers the ingest just
    committed, so the registry cannot describe a vintage that is not in the
    database.
    """
    if not registry_path.exists():
        return f"cadence registry not found: {registry_path}"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return f"cadence registry unreadable: {exc}"

    foodberg = registry.get("foodberg")
    if not isinstance(foodberg, dict):
        return "cadence registry has no 'foodberg' entry to extend"

    last_report = stats.get("last_report_date")
    if last_report:
        next_due = next_business_day(dt.date.fromisoformat(last_report)).isoformat()
    else:
        next_due = None

    source_line = (
        "USDA AMS Market News (MARS API v3.1) — daily terminal-market wholesale "
        "fruit & vegetable prices (ams_wholesale_prices) — every business day"
    )
    sources = foodberg.setdefault("sources", [])
    if source_line not in sources:
        # Replace any earlier AMS line rather than accumulating duplicates.
        sources[:] = [s for s in sources if "AMS Market News" not in s]
        sources.append(source_line)

    slug_ids = stats.get("slugs") or []
    per_source = foodberg.setdefault("per_source", {})
    per_source["usda_ams_market_news"] = {
        "table": TABLE,
        "source": source_line,
        "publisher": "USDA Agricultural Marketing Service, Market News",
        "publisher_series_ids": (
            f"{len(slug_ids)} terminal-market report streams, each addressed by "
            f"its NUMERIC slug_id (slug_name=slug_id): {', '.join(slug_ids)}"
        ),
        "landing": PROGRAMME_LANDING,
        "licence": "U.S. Government work (public domain)",
        "refresh_cadence": "daily (business days)",
        "method": (
            "Technical/scripts/ingest_ams.py pulls MARS v3.1 "
            "/reports/{slug_id}/Report Details for every ACTIVE terminal-market "
            "stream in the live catalog (discontinued markets are detected from "
            "the catalog status field, not a hardcoded list) and writes "
            "ams_wholesale_prices with INSERT OR IGNORE against a UNIQUE "
            "row_hash digest of the whole price line. Idempotent and resumable; "
            "this registry entry is written in the same run as the ingest, from "
            "row counts queried out of the database it just committed."
        ),
        "last_updated": stats.get("last_report_date"),
        "last_updated_basis": (
            f"{TABLE}: {stats['rows']:,} rows, {stats['cities']} cities, "
            f"{stats['commodities']} commodities, {stats['report_streams']} report "
            f"streams, report_date span {stats['first_report_date']} .. "
            f"{stats['last_report_date']} (counted from backend/data/foodberg.db "
            f"at {dt.datetime.now(dt.timezone.utc).isoformat()})"
        ),
        "next_due": next_due,
        "next_due_note": (
            "AMS publishes terminal-market prices every business day; the next "
            "run is due the business day after the newest stored report_date."
        ),
        "refresh_skill": "Technical/scripts/ingest_ams.py",
        "surfaced_on": ["/api/wholesale/search", "/api/wholesale/markets", "/downloads"],
    }

    registry_path.write_text(
        json.dumps(registry, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_day(value: str) -> dt.date:
    value = value.strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f"unrecognised date {value!r} (use MM/DD/YYYY)")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--days", type=int, default=None,
                    help="ingest the last N days (default 365 when no range given)")
    ap.add_argument("--start", type=parse_day, default=None, help="MM/DD/YYYY")
    ap.add_argument("--end", type=parse_day, default=None, help="MM/DD/YYYY")
    ap.add_argument("--full-history", action="store_true",
                    help="probe the API's earliest served year and load from there")
    ap.add_argument("--markets", default=None,
                    help="comma-separated city keys (e.g. new_york,chicago); "
                         "default = every ACTIVE terminal market in the catalog")
    ap.add_argument("--families", default=None,
                    help="comma-separated report families (FV010,FV020,FV030,FV040)")
    ap.add_argument("--include-discontinued", action="store_true")
    ap.add_argument("--state", type=Path, default=DEFAULT_STATE)
    ap.add_argument("--restart", action="store_true",
                    help="ignore the resume checkpoint and re-walk every window")
    ap.add_argument("--batch-rows", type=int, default=5000)
    ap.add_argument("--delay", type=float, default=0.2,
                    help="minimum seconds between API requests")
    ap.add_argument("--no-cadence", action="store_true",
                    help="skip the Carson cadence-registry update")
    ap.add_argument("--cadence-only", action="store_true",
                    help="re-derive the cadence entry from the database without "
                         "fetching (use after a multi-batch load)")
    ap.add_argument("--list-markets", action="store_true",
                    help="print the catalog-derived market list and exit")
    args = ap.parse_args(argv)

    if args.cadence_only:
        con = connect(args.db)
        try:
            stats = table_stats(con)
        finally:
            con.close()
        note = update_cadence_registry(CADENCE_REGISTRY, stats)
        if note:
            print(f"cadence registry NOT updated - {note}", file=sys.stderr)
            return 1
        print(f"cadence registry updated from {stats['rows']:,} rows "
              f"({stats['first_report_date']} .. {stats['last_report_date']})")
        return 0

    client = USDAMarketNewsClient(request_delay=args.delay)
    families = [f.strip().upper() for f in args.families.split(",")] if args.families else None
    streams = client.list_terminal_markets(
        families=families, include_discontinued=args.include_discontinued
    )

    if args.markets:
        wanted = {m.strip().lower().replace(" ", "_") for m in args.markets.split(",")}
        streams = [s for s in streams if s["key"] in wanted]
        missing = wanted - {s["key"] for s in streams}
        if missing:
            print(f"unknown market key(s): {', '.join(sorted(missing))}", file=sys.stderr)
            print(f"available: {', '.join(client.market_keys())}", file=sys.stderr)
            return 2

    if args.list_markets:
        for s in streams:
            print(f"{s['slug_id']:>5}  {s['slug_name']:<10} {s['key']:<14} "
                  f"{s['family_label']:<20} {s['city']}, {s['state']}  "
                  f"latest={s['latest_report_date']}")
        print(f"\n{len(streams)} streams across {len({s['key'] for s in streams})} cities")
        return 0

    if not streams:
        print("no report streams selected", file=sys.stderr)
        return 2

    # ---- date range -----------------------------------------------------
    end = args.end or dt.date.today()
    if args.full_history:
        reference = next(
            (s for s in streams if s["family"] == "FV020"), streams[0]
        )
        print("probing how far back the API serves Report Details ...")
        start = probe_history_floor(client, reference["slug_id"])
    elif args.start:
        start = args.start
    else:
        start = end - dt.timedelta(days=(args.days or 365))
    if start > end:
        print("start is after end", file=sys.stderr)
        return 2

    if not args.db.exists():
        print(f"database not found: {args.db}", file=sys.stderr)
        return 2

    state_path = args.state
    state = {"version": 1, "completed": {}} if args.restart else load_state(state_path)

    con = connect(args.db)
    status = "SUCCESS"
    error_message: Optional[str] = None
    try:
        ensure_schema(con)
        result = ingest(
            con, client, streams, start, end, state, state_path,
            batch_rows=args.batch_rows,
        )
        stats = table_stats(con)

        if result["errors"]:
            status = "PARTIAL"
            error_message = (
                f"{len(result['errors'])} window(s) failed; first: {result['errors'][0]}"
            )
        elif stats["rows"] == 0:
            status = "NO_DATA"

        next_due = (
            next_business_day(dt.date.fromisoformat(stats["last_report_date"])).isoformat()
            if stats["last_report_date"] else None
        )
        record_sync(con, status, stats["rows"], error_message, next_due)
    finally:
        con.close()

    # The cadence registry is refreshed from the numbers the ingest just
    # committed, in this same run — never from a separate later pass.
    cadence_note = None
    if not args.no_cadence and status in ("SUCCESS", "PARTIAL"):
        cadence_note = update_cadence_registry(CADENCE_REGISTRY, stats)

    print()
    print("=" * 72)
    print(f"AMS ingest status        : {status}")
    print(f"  requests planned       : {result['requests_planned']}")
    print(f"  resumed (skipped)      : {result['requests_skipped_resumed']}")
    print(f"  line items fetched     : {result['line_items_fetched']:,}")
    print(f"  rows inserted this run : {result['rows_inserted']:,}")
    print(f"  window errors          : {len(result['errors'])}")
    print(f"{TABLE} now holds:")
    for k, v in stats.items():
        if k == "slugs":
            continue
        print(f"  {k:<20} : {v:,}" if isinstance(v, int) else f"  {k:<20} : {v}")
    print(f"data_source_sync['{SOURCE_NAME}'] = {status} / {stats['rows']:,} rows")
    if cadence_note:
        print(f"cadence registry       : NOT UPDATED - {cadence_note}")
    elif not args.no_cadence:
        print(f"cadence registry       : updated {CADENCE_REGISTRY}")
    print("=" * 72)

    return 0 if status in ("SUCCESS", "PARTIAL") else 1


if __name__ == "__main__":
    raise SystemExit(main())
