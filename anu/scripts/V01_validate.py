#!/usr/bin/env python3
"""V01 — Validate the final output against series_registry.json.

Checks, per registry entry:
  1. PRESENCE  — the expected output file exists (family entries -> one long
                 CSV named <family>.csv at data/final/ root).
  2. NONEMPTY  — at least one observation; required column has no nulls.
  3. COVERAGE  — actual date range CONTAINS the declared range (with a
                 2-month slack at the end for publication lags).
  4. SANITY    — values are numeric and finite; price/index series must be
                 non-negative. Negative values FAIL; zero values WARN (the
                 publisher itself prints 0.0 for unquoted months, e.g. Thai
                 25% rice during Thailand's 2008 export ban).
  5. COUNT     — number of non-family files produced equals the number of
                 non-family registry entries expected in each bucket
                 (files for entries not in the registry are a WARNING).
  6. OPTIONAL  — entries flagged "optional" (the NASS family, which needs a
                 free API key) are validated only when their file exists.

Exit code 0 = all pass; 1 = any FAIL. `--allow-missing prefix[,prefix...]`
downgrades PRESENCE failures for the named series-id prefixes to warnings
(used by `make quick` to skip the two ~200 MB FAOSTAT bulk downloads).
"""

import csv
import math
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import FINAL, load_registry  # noqa: E402

SLACK_MONTHS = 2
FAMILY_MIN_ROWS = 10_000          # FAOSTAT families; NASS optional family
NASS_MIN_ROWS = 1_000
VALUE_COL = {"retail": "price",
            "faostat_producer_prices.csv": "value_usd_tonne"}


def bucket_of(entry: dict) -> str:
    """Output bucket derived from the last P## script in construction.scripts."""
    scripts = entry["construction"]["scripts"]
    p = [s for s in scripts
         if s.startswith("P") and ("construct" in s or "harmonise" in s)]
    if not p:
        return ""
    last = p[-1]
    for tag, bucket in (("P01", "pink_sheet"), ("P03", "fpi"),
                        ("P04", "indicators"), ("P05", "retail"),
                        ("P06", "composites")):
        if tag in last:
            return bucket
    return ""


def month_key(s: str) -> date:
    return date.fromisoformat(s[:10])


def declared_keys(cov: dict):
    """(start_date, end_date, year_granularity) or (None, None, False)."""
    start, end = str(cov.get("start", "")), str(cov.get("end", ""))
    year_gran = len(start) == 4 and start.isdigit()
    s = date.fromisoformat(f"{start}-01-01") if year_gran else (
        month_key(f"{start}-01") if len(start) == 7 else None)
    if len(end) == 4 and end.isdigit():
        e = date.fromisoformat(f"{end}-01-01")
        year_gran = True
    else:
        e = month_key(f"{end}-01") if len(end) == 7 else None
    return s, e, year_gran


def month_add(d: date, months: int) -> date:
    y, m = d.year + (d.month - 1 + months) // 12, (d.month - 1 + months) % 12 + 1
    return date(y, m, 1)


def validate_file(path: Path, entry: dict, results: list) -> None:
    sid = entry["series_id"]
    vcol = VALUE_COL.get(path.name, VALUE_COL.get(path.parent.name, "value"))
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    if not rows:
        results.append((sid, "FAIL", "no data rows"))
        return
    if vcol not in rows[0]:
        results.append((sid, "FAIL", f"missing column {vcol}"))
        return
    dates, bad, negatives, zeros, nonnum = [], 0, 0, 0, 0
    for r in rows:
        raw = (r.get(vcol) or "").strip()
        try:
            v = float(raw)
        except ValueError:
            nonnum += 1
            continue
        if not math.isfinite(v):
            nonnum += 1
            continue
        if v < 0:
            negatives += 1
        elif v == 0:
            zeros += 1
        d = (r.get("date") or "").strip()
        if d:
            dates.append(d)
    if nonnum:
        results.append((sid, "FAIL", f"{nonnum} non-numeric values"))
        return
    if negatives:
        results.append((sid, "FAIL", f"{negatives} negative {vcol} values"))
        return
    if zeros:
        results.append((sid, "WARN",
                        f"{zeros} zero values (publisher no-quote months)"))
    if not dates:
        results.append((sid, "FAIL", "no parseable dates"))
        return
    ds_min, ds_max = min(dates), max(dates)
    want_s, want_e, year_gran = declared_keys(entry["coverage"])
    msgs = []
    if want_s:
        ok = (month_key(ds_min).year <= want_s.year) if year_gran \
            else (month_key(ds_min) <= want_s)
        if not ok:
            msgs.append(f"starts {ds_min} later than declared "
                        f"{entry['coverage']['start']}")
    if want_e:
        ok = (month_key(ds_max).year >= want_e.year) if year_gran \
            else (month_key(ds_max) >= month_add(want_e, -SLACK_MONTHS))
        if not ok:
            msgs.append(f"ends {ds_max} earlier than declared "
                        f"{entry['coverage']['end']}"
                        + (f" (beyond {SLACK_MONTHS}-month slack)" if not year_gran else ""))
    for m in msgs:
        results.append((sid, "FAIL", m))
    if not msgs:
        n = entry.get("_min_rows")
        if n and len(rows) < n:
            results.append((sid, "FAIL", f"{len(rows)} rows < required {n}"))
            return
        results.append((sid, "PASS",
                        f"{len(rows)} obs {ds_min}..{ds_max}"))


def main() -> int:
    allow = set()
    if "--allow-missing" in sys.argv:
        allow = {p.strip() for p in
                 sys.argv[sys.argv.index("--allow-missing") + 1].split(",")}
    reg = load_registry()["series"]
    results, missing = [], []
    expected_files: dict = {}  # bucket -> set of sids

    for e in reg:
        sid = e["series_id"]
        family = e.get("family")
        if family:
            path = FINAL / f"{family}.csv"
            min_rows = NASS_MIN_ROWS if family == "usda_nass_wasde" else FAMILY_MIN_ROWS
            e = dict(e, _min_rows=min_rows)
        else:
            bucket = bucket_of(e)
            if not bucket:
                results.append((sid, "FAIL", "cannot derive output bucket"))
                continue
            path = FINAL / bucket / f"{sid}.csv"
            expected_files.setdefault(bucket, set()).add(sid)
        if not path.exists():
            if e.get("optional"):
                results.append((sid, "SKIP", "optional family absent"))
            elif any(sid.startswith(p) for p in allow):
                results.append((sid, "WARN", "absent (allowed via --allow-missing)"))
            else:
                missing.append(sid)
                results.append((sid, "FAIL", f"missing output {path.relative_to(FINAL.parent)}"))
            continue
        validate_file(path, e, results)

    # COUNT check: stray files per bucket are warnings
    for bucket, sids in expected_files.items():
        bdir = FINAL / bucket
        if not bdir.is_dir():
            continue
        for f in bdir.glob("*.csv"):
            if f.stem not in sids:
                results.append((f.stem, "WARN",
                                f"file in {bucket}/ not in registry"))

    n_pass = sum(1 for r in results if r[1] == "PASS")
    n_warn = sum(1 for r in results if r[1] == "WARN")
    n_skip = sum(1 for r in results if r[1] == "SKIP")
    n_fail = sum(1 for r in results if r[1] == "FAIL")
    for sid, status, msg in results:
        if status != "PASS":
            print(f"[V01] {status} {sid}: {msg}")
    print(f"[V01] PASS={n_pass} WARN={n_warn} SKIP={n_skip} FAIL={n_fail} "
          f"(registry: {len(reg)} entries)")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
