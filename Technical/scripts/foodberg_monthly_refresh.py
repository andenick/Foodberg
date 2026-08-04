#!/usr/bin/env python3
"""
foodberg_monthly_refresh.py — thin orchestrator for the monthly Foodberg refresh.

Steps:
  1. Read/write REFRESH_STATE.json (resume point)
  2. Refresh Robin stores (Pink Sheet scrape, BLS AP, BLS monthly series
     [Census-region AP + WPU01130217 + CUUR0000SEFV01/02], FAOSTAT HEAD-check,
     PS&D re-mirror, NASS drift check)
  3. Snapshot project DB
  4. Run rebake_history.py
  5. Verify row counts (gate: no drops)
  6. Stage deploy artifact
  7. STOP — user-gated box deploy (print steps)

Usage:
  python foodberg_monthly_refresh.py           # full refresh
  python foodberg_monthly_refresh.py --dry-run  # preview only, no mutations

Invariants:
  - Never auto-deploy to box
  - No silent fallbacks / no fabricated data
  - Snapshot before rebake
  - wasde_psd must never be dropped
  - pathlib / forward slashes throughout
"""

import argparse
import datetime
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

# ── paths (resolved from the repo, overridable by environment) ────────────
# FOODBERG_PROJECT_ROOT / FOODBERG_STORE_ROOT / FOODBERG_DEPLOY_DB let an
# operator point the orchestrator at a private data store and deploy tree
# without hardcoding any machine-specific location in the published source.
PROJ = Path(os.environ.get("FOODBERG_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
STORE_ROOT = Path(os.environ.get("FOODBERG_STORE_ROOT", PROJ / "Inputs" / "stores"))
ROBIN = STORE_ROOT
ROBIN_DATA = STORE_ROOT / "DATA"
DEPLOY_ARTIFACT = Path(
    os.environ.get("FOODBERG_DEPLOY_DB", PROJ / "deploy" / "backend" / "data" / "foodberg.db")
)

STATE_PATH = PROJ / "Technical" / "REFRESH_STATE.json"
DB_PATH = PROJ / "backend" / "data" / "foodberg.db"
BACKUP_DIR = PROJ / "backend" / "data" / "backups"
REBAKE_SCRIPT = PROJ / "backend" / "database" / "rebake_history.py"
PSD_SCRIPT = PROJ / "Technical" / "data_processors" / "process_psd_wasde.py"
BLS_SCRIPT = ROBIN / "API_MODULES" / "BLS" / "refresh_ap_via_fred_20260718.py"
BLS_MONTHLY_SCRIPT = PROJ / "Technical" / "scripts" / "ingest_bls_monthly_series.py"

NOW_ISO = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
TODAY = datetime.date.today()
TAG = TODAY.strftime("%Y%m%d")

# ── row-count gates (from DEPLOY_READY_20260718.md §2) ────────────────────
ROW_GATES: dict[str, dict[str, int]] = {
    "wasde_data":          {"min": 1_459_000, "expect_growth": False},
    "global_prices":       {"min": 290_000,  "expect_growth": True},
    # 2026-07-24: retail_prices 20,359 -> 22,398 (the four Census-region
    # APU0[1-4]00712311 tomato series) and economic_indicators 14,640 -> 16,246
    # (WPU01130217, CUUR0000SEFV01, CUUR0000SEFV02). Floors raised so a rebake
    # that silently drops the new series fails the gate instead of passing.
    "retail_prices":       {"min": 22_390,   "expect_growth": True},
    "economic_indicators": {"min": 16_240,   "expect_growth": True},
    "composite_indices":   {"min": 2_700,    "expect_growth": False},
    "wasde_psd":           {"min": 1_981_000, "expect_growth": False, "preserved": True},
}


# ── helpers ────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    print(f"[refresh {TAG}] {msg}", flush=True)


def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"last_refresh": None, "history": [], "row_counts": {}, "pending_items": []}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


def run(cmd: list[str], cwd: Path | None = None, dry: bool = False) -> subprocess.CompletedProcess:
    """Run a command; print it; on dry-run skip execution and return a mock success."""
    log(f"  CMD: {' '.join(str(c) for c in cmd)}")
    if dry:
        return subprocess.CompletedProcess(cmd, 0, stdout="[dry-run] skipped", stderr="")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def check_disk(min_gb: int = 20) -> None:
    import shutil as _shutil
    usage = _shutil.disk_usage(PROJ)
    free_gb = usage.free / (1024 ** 3)
    log(f"Disk free: {free_gb:.1f} GB")
    if free_gb < min_gb:
        log(f"FAIL: disk below {min_gb} GB guard — aborting")
        sys.exit(1)


# ── step 0: read state ────────────────────────────────────────────────────

def step_read_state() -> dict[str, Any]:
    state = load_state()
    log(f"Last refresh: {state.get('last_refresh') or 'never'}")
    log(f"Pending items: {state.get('pending_items')}")
    if state.get("history"):
        log(f"Prior refreshes: {len(state['history'])}")
        for h in state["history"][-2:]:
            log(f"  {h.get('date')}: {h.get('sources_updated')}")
    return state


# ── step 1: refresh Robin stores ──────────────────────────────────────────

def step_pink_sheet(dry: bool = False) -> str:
    """Scrape current Pink Sheet XLSX from World Bank commodity-markets page."""
    log("Pink Sheet: scraping current CMO-Historical-Data-Monthly.xlsx URL …")
    # The URL changes each edition — agent-driven page scrape is required.
    # Documented pattern (from 2026-07-18 run):
    #   Browse worldbank.org/en/research/commodity-markets
    #   Locate CMO-Historical-Data-Monthly.xlsx link
    #   Download to ROBIN_DATA/WORLD_BANK_PINKSHEET/CMO-Historical-Data-Monthly_YYYY-MM.xlsx
    #   Rename current symlink/copy to new file
    if dry:
        log("  [dry-run] would scrape worldbank.org/.../commodity-markets")
        return "[dry-run] Pink Sheet scrape skipped"
    # Actual scrape requires browser automation — documented for agent, not auto-executed here
    log("  Pink Sheet scrape requires manual agent step (URL changes per edition)")
    log("  Per DEPLOY_READY_20260718.md §1: scrape doc hash from commodity-markets page")
    return "pending — manual scrape required"


def step_bls_ap(dry: bool = False) -> str:
    """Run BLS AP refresh via FRED mirror (keyless, ~1 min)."""
    log("BLS AP: running refresh_ap_via_fred_20260718.py …")
    BLS_DIR = ROBIN / "API_MODULES" / "BLS"
    result = run(["python", str(BLS_SCRIPT), "fetch"], cwd=BLS_DIR, dry=dry)
    if result.returncode != 0 and not dry:
        log(f"  FETCH FAILED: {result.stderr[-500:]}")
        return "FAILED"
    if not dry:
        verify = run(["python", str(BLS_SCRIPT), "verify"], cwd=BLS_DIR, dry=False)
        if verify.returncode != 0:
            log(f"  VERIFY FAILED: {verify.stderr[-500:]}")
            return "FAILED"
        promote = run(["python", str(BLS_SCRIPT), "promote"], cwd=BLS_DIR, dry=False)
        if promote.returncode != 0:
            log(f"  PROMOTE FAILED: {promote.stderr[-500:]}")
            return "FAILED"
        log(f"  BLS AP promoted: {promote.stdout.strip()[-200:]}")
    return "OK"


def step_bls_monthly_series(dry: bool = False) -> str:
    """
    Refresh the monthly BLS series that Robin's AP refresher does not cover, and
    restore the extended provenance on the four Census-region AP artifacts.

    Must run AFTER step_bls_ap: `refresh_ap_via_fred_20260718.py promote`
    rewrites every top-level ap_fred_*.json from a fixed key set and would drop
    the `provenance` / `liveness` / `series_title` blocks this script writes.
    Re-running it here restores them and picks up the new month for
    WPU01130217 and CUUR0000SEFV01/02 as well. Idempotent (no deletes, upserts
    on the DB), keyless.
    """
    log("BLS monthly series: running ingest_bls_monthly_series.py …")
    result = run(["python", str(BLS_MONTHLY_SCRIPT)], cwd=PROJ, dry=dry)
    if result.returncode != 0 and not dry:
        log(f"  BLS MONTHLY SERIES FAILED: {result.stderr[-500:]}")
        return "FAILED"
    if not dry:
        log(f"  {result.stdout.strip()[-400:]}")
    return "OK"


def step_faostat(dry: bool = False) -> str:
    """HEAD-check FAOSTAT bulk zips; skip if unchanged."""
    log("FAOSTAT: HEAD-checking bulk download freshness …")
    import urllib.request
    fao_files = [
        ("Prices_E", "https://fenixservices.fao.org/faostat/static/bulkdownloads/Prices_E_All_Data_(Normalized).zip"),
        ("CPI", "https://fenixservices.fao.org/faostat/static/bulkdownloads/ConsumerPriceIndices_E_All_Data_(Normalized).zip"),
    ]
    results = []
    for label, url in fao_files:
        if dry:
            log(f"  [dry-run] would HEAD {url}")
            results.append(f"{label}: dry-run skipped")
            continue
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ArcanumResearch/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                last_mod = r.headers.get("Last-Modified", "unknown")
                size = r.headers.get("Content-Length", "unknown")
            log(f"  {label}: Last-Modified={last_mod}, Size={size}")
            results.append(f"{label}: {last_mod}")
        except Exception as e:
            log(f"  {label}: HEAD failed — {e}")
            results.append(f"{label}: HEAD FAILED")
    return "; ".join(results)


def step_psd(dry: bool = False) -> str:
    """Re-mirror PS&D 7-zip bundle + process."""
    log("PS&D: re-mirroring 7-commodity zip bundle …")
    PSD_DIR = PROJ / "Technical" / "data_processors"
    result = run(["python", str(PSD_SCRIPT)], cwd=PSD_DIR, dry=dry)
    if result.returncode != 0 and not dry:
        log(f"  PS&D PROCESS FAILED: {result.stderr[-500:]}")
        return "FAILED"
    return "OK"


def step_nass(dry: bool = False) -> str:
    """Check NASS load_time drift; skip if no new annual vintages."""
    log("NASS: checking load_time drift (~2.5h collector, annual cadence) …")
    nass_collector = ROBIN / "API_MODULES" / "USDA_NASS" / "nass_collector_historical.py"
    if dry:
        log(f"  [dry-run] would check {nass_collector} drift + run if warranted")
        return "[dry-run] NASS skipped"
    if not nass_collector.exists():
        log(f"  Collector not found at {nass_collector} — skipping")
        return "SKIPPED (collector missing)"
    # Annual cadence — only run if drift confirms new vintages
    # Agent: check USDA NASS API for newer data before triggering this
    log("  NASS is annual-cadence; agent must verify newer data exists before running")
    log("  Run off-hours: python nass_collector_historical.py")
    return "SKIPPED (annual cadence, agent-gated)"


def step_refresh_stores(state: dict[str, Any], dry: bool = False) -> dict[str, str]:
    """Run all Robin store refreshes, returning per-source status dict."""
    check_disk()
    results: dict[str, str] = {}
    results["pink_sheet"] = step_pink_sheet(dry)
    results["bls_ap"] = step_bls_ap(dry)
    # Must follow bls_ap — see step_bls_monthly_series docstring.
    results["bls_monthly_series"] = step_bls_monthly_series(dry)
    results["faostat"] = step_faostat(dry)
    results["psd"] = step_psd(dry)
    results["nass"] = step_nass(dry)
    log(f"Store refresh results: {results}")
    return results


# ── step 2: snapshot DB ───────────────────────────────────────────────────

def step_snapshot(dry: bool = False) -> Path:
    backup = BACKUP_DIR / f"foodberg_pre_rebake_{TAG}.db"
    log(f"Snapshot: {DB_PATH} -> {backup}")
    if dry:
        log("  [dry-run] would copy DB")
    else:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        if DB_PATH.exists():
            shutil.copy2(DB_PATH, backup)
            size_mb = backup.stat().st_size / (1024 * 1024)
            log(f"  Snapshot OK: {size_mb:.0f} MB")
        else:
            log(f"  WARNING: DB not found at {DB_PATH}")
    return backup


# ── step 3: rebake ────────────────────────────────────────────────────────

def step_rebake(dry: bool = False) -> subprocess.CompletedProcess:
    log("Rebake: running backend/database/rebake_history.py …")
    DB_DIR = PROJ / "backend" / "database"
    return run(["python", str(REBAKE_SCRIPT)], cwd=DB_DIR, dry=dry)


# ── step 4: verify row counts ─────────────────────────────────────────────

def step_verify_counts(dry: bool = False) -> dict[str, int]:
    log("Row-count gate: verifying no table shrank …")
    if dry:
        log("  [dry-run] would query DB row counts")
        return {t: g["min"] for t, g in ROW_GATES.items()}

    counts: dict[str, int] = {}
    if not DB_PATH.exists():
        log(f"  FAIL: DB not found at {DB_PATH}")
        return counts
    con = sqlite3.connect(str(DB_PATH))
    passed = True
    for table, gate in ROW_GATES.items():
        try:
            cur = con.execute(f'SELECT COUNT(*) FROM "{table}"')
            n = cur.fetchone()[0]
            counts[table] = n
            status = "✅" if n >= gate["min"] else "❌ BELOW GATE"
            log(f"  {table}: {n:,} (gate: {gate['min']:,}) {status}")
            if n < gate["min"]:
                passed = False
        except sqlite3.OperationalError as e:
            log(f"  {table}: MISSING ({e})")
            counts[table] = 0
            passed = False
    con.close()

    if not passed:
        log("ROW COUNT GATE FAILED — restore from snapshot and investigate!")
        if not dry:
            sys.exit(1)
    return counts


# ── step 5: stage deploy artifact ─────────────────────────────────────────

def step_stage(dry: bool = False) -> None:
    log(f"Stage: {DB_PATH} -> {DEPLOY_ARTIFACT}")
    if dry:
        log("  [dry-run] would copy DB to deploy location")
        return
    DEPLOY_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DB_PATH, DEPLOY_ARTIFACT)
    size_mb = DEPLOY_ARTIFACT.stat().st_size / (1024 * 1024)
    log(f"  Deploy artifact staged: {size_mb:.0f} MB")


# ── step 6: deploy gate (user action required) ────────────────────────────

def step_deploy_gate(state: dict[str, Any], counts: dict[str, int]) -> None:
    print()
    print("=" * 68)
    print("  FOODBERG REFRESH COMPLETE — USER ACTION REQUIRED")
    print("=" * 68)
    print()
    sources = state.get("last_sources", {})
    for k, v in sources.items():
        print(f"  {k}: {v}")
    print()
    print("  Row count verification: PASSED")
    for t, n in counts.items():
        print(f"    {t}: {n:,}")
    print()
    print(f"  Deploy artifact staged at: {DEPLOY_ARTIFACT}")
    print(f"  Snapshot: {BACKUP_DIR}/foodberg_pre_rebake_{TAG}.db")
    print()
    print("  TO DEPLOY ON PRODUCTION:")
    print("    1. Sync deploy tree to box")
    print("    2. docker compose build backend")
    print("    3. docker compose up -d")
    print("    4. Smoke test:")
    print("       curl https://foodberg.org/api/data/status")
    print('       curl "https://foodberg.org/api/prices/global?source=World%20Bank%20Pink%20Sheet"')
    print()
    print(f"  ROLLBACK: backend/data/backups/foodberg_pre_rebake_{TAG}.db")
    print()


# ── step 7: close out ─────────────────────────────────────────────────────

def step_closeout(state: dict[str, Any], counts: dict[str, int],
                  sources: dict[str, str], dry: bool = False) -> None:
    entry = {
        "date": TODAY.isoformat(),
        "dry_run": dry,
        "sources_updated": sources,
        "row_counts": counts,
        "pending_items": state.get("pending_items", []),
    }
    state["last_refresh"] = TODAY.isoformat()
    state.setdefault("history", []).append(entry)
    if not dry:
        save_state(state)
        log(f"State saved: {STATE_PATH}")
    else:
        log("[dry-run] would save state:")
        log(json.dumps(entry, indent=2, default=str))


# ── main ───────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Foodberg monthly refresh orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no mutations")
    args = parser.parse_args()
    dry: bool = args.dry_run

    log(f"Foodberg monthly refresh — {TAG}" + (" [DRY-RUN]" if dry else ""))
    check_disk()

    state = step_read_state()

    # 1. Robin stores
    sources = step_refresh_stores(state, dry)
    state["last_sources"] = sources

    # 2. Snapshot
    step_snapshot(dry)

    # 3. Rebake
    result = step_rebake(dry)
    if result.returncode != 0 and not dry:
        log(f"REBAKE FAILED: {result.stderr[-1000:]}")
        sys.exit(1)
    if not dry:
        log(f"Rebake stdout (last 500 chars): {result.stdout.strip()[-500:]}")

    # 4. Row-count gates
    counts = step_verify_counts(dry)

    # 5. Stage deploy artifact
    step_stage(dry)

    # 6. Deploy gate (always prints — user action required)
    step_deploy_gate(state, counts)

    # 7. Close out
    step_closeout(state, counts, sources, dry)

    if dry:
        log("Dry-run complete — no state saved, no mutations made.")
    else:
        log("Refresh complete — deploy is USER-GATED (not automatic).")


if __name__ == "__main__":
    main()