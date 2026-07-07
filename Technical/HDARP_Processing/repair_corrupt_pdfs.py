"""
PDF Corruption Scanner & Repairer — Foodberg Project
======================================================
Phase 1: Scan all PDFs in PDF_MANIFEST.csv for corruption (zero pages / unreadable)
Phase 2: Repair with pikepdf (qpdf engine)
Phase 3: Fallback repairs with PyMuPDF (fitz) save
Phase 4: Report unrecoverable PDFs

Usage:
    D:\Arcanum\Projects\Foodberg\backend\venv\Scripts\python.exe repair_corrupt_pdfs.py
"""

import csv
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────
PROJECT_ROOT = Path(r"D:\Arcanum\Projects\Foodberg")
MANIFEST_PATH = PROJECT_ROOT / "Technical" / "HDARP_Processing" / "PDF_MANIFEST.csv"
LOG_PATH = PROJECT_ROOT / "Technical" / "HDARP_Processing" / "PDF_REPAIR_LOG.md"
UNRECOVERABLE_PATH = PROJECT_ROOT / "Technical" / "HDARP_Processing" / "CORRUPT_UNRECOVERABLE.csv"
OUTPUT_MANIFEST_PATH = PROJECT_ROOT / "Technical" / "HDARP_Processing" / "PDF_MANIFEST.csv"  # in-place update

# Part directories to scan
INPUT_DIRS = [
    PROJECT_ROOT / "Inputs" / "2026.04.12 Foodberg Pdfs Part 1" / "2026.04.12 Foodberg Pdfs",
    PROJECT_ROOT / "Inputs" / "2026.04.12 Foodberg Pdfs Part 2" / "2026.04.12 Foodberg Pdfs",
]

START_TIME = datetime.now()

# ── Helpers ────────────────────────────────────────────────────────

def log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

def test_pdf_with_fitz(path: Path) -> tuple:
    """Try to open a PDF with PyMuPDF. Returns (readable: bool, page_count: int, error: str)."""
    import fitz
    try:
        doc = fitz.open(str(path))
        n = len(doc)
        doc.close()
        return (True, n, "")
    except Exception as e:
        return (False, 0, str(e)[:200])

def repair_with_pikepdf(path: Path) -> bool:
    """Attempt to repair a PDF using pikepdf (qpdf engine). Overwrites in place."""
    import pikepdf
    try:
        pdf = pikepdf.open(str(path), allow_overwriting_input=True)
        pdf.save(str(path))
        pdf.close()
        return True
    except Exception:
        return False

def repair_with_pikepdf_to_new(corrupt_path: Path, output_path: Path) -> bool:
    """Attempt to repair by saving to a new file (for structured corruption)."""
    import pikepdf
    try:
        pdf = pikepdf.open(str(corrupt_path))
        pdf.save(str(output_path))
        pdf.close()
        return True
    except Exception:
        return False

def repair_with_fitz_save(path: Path) -> bool:
    """Fallback: try to open with fitz and save a clean copy via garbage collection."""
    import fitz
    try:
        doc = fitz.open(str(path))
        tmp = str(path) + ".repaired_tmp"
        doc.save(tmp, garbage=4, deflate=True)
        doc.close()
        # Replace original
        os.replace(tmp, str(path))
        return True
    except Exception:
        # Clean up tmp if it exists
        tmp = str(path) + ".repaired_tmp"
        if os.path.exists(tmp):
            os.remove(tmp)
        return False


# ── Phase 1: SCAN ──────────────────────────────────────────────────

def scan_all_pdfs():
    """Scan all PDFs listed in manifest. Return {pdf_path: (readable, pages, error)}."""
    log("=== PHASE 1: Scanning all PDFs for corruption ===")
    
    results = {}
    
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    log(f"Loaded {len(rows)} rows from manifest")
    
    total = len(rows)
    for i, row in enumerate(rows):
        pdf_path = Path(row["pdf_path"])
        
        if (i + 1) % 50 == 0:
            log(f"  Scan progress: {i+1}/{total}")
        
        if not pdf_path.exists():
            results[row["pdf_path"]] = (False, -1, "FILE_NOT_FOUND")
            continue
        
        readable, pages, error = test_pdf_with_fitz(pdf_path)
        results[row["pdf_path"]] = (readable, pages, error)
    
    # Summarize
    corrupt = {k: v for k, v in results.items() if not v[0] or v[1] == 0}
    healthy = {k: v for k, v in results.items() if v[0] and v[1] > 0}
    
    log(f"Scan complete: {len(healthy)} healthy, {len(corrupt)} corrupt/zero-page")
    
    return results, rows, corrupt, healthy


# ── Phase 2: REPAIR ────────────────────────────────────────────────

def repair_corrupt_pdfs(corrupt: dict):
    """Repair all corrupt PDFs. Returns {pdf_path: repair_status}."""
    log(f"\n=== PHASE 2: Repairing {len(corrupt)} corrupt PDFs ===")
    
    repair_results = {}
    stats = {"pikepdf_fixed": 0, "pikepdf_new_fixed": 0, "fitz_fixed": 0, "unrecoverable": 0}
    
    total = len(corrupt)
    for i, (pdf_path_str, (_, _, error)) in enumerate(corrupt.items()):
        pdf_path = Path(pdf_path_str)
        filename = pdf_path.name
        
        if (i + 1) % 10 == 0:
            log(f"  Repair progress: {i+1}/{total} (pikepdf={stats['pikepdf_fixed']}, fitz={stats['fitz_fixed']}, unrecoverable={stats['unrecoverable']})")
        
        # Skip files that don't exist
        if not pdf_path.exists():
            repair_results[pdf_path_str] = {
                "status": "unrecoverable",
                "method": "none",
                "error": "FILE_NOT_FOUND",
                "pages_after": -1,
            }
            stats["unrecoverable"] += 1
            continue
        
        size_before = pdf_path.stat().st_size
        repaired = False
        
        # ── Strategy 1: pikepdf repair in-place ──
        if repair_with_pikepdf(pdf_path):
            readable, pages, err = test_pdf_with_fitz(pdf_path)
            if readable and pages > 0:
                size_after = pdf_path.stat().st_size
                repair_results[pdf_path_str] = {
                    "status": "repaired",
                    "method": "pikepdf_inplace",
                    "error": "",
                    "pages_after": pages,
                    "size_before": size_before,
                    "size_after": size_after,
                }
                stats["pikepdf_fixed"] += 1
                repaired = True
        
        # ── Strategy 2: pikepdf save-to-new (for structured corruption) ──
        if not repaired:
            tmp_path = Path(str(pdf_path) + ".pikepdf_tmp")
            if repair_with_pikepdf_to_new(pdf_path, tmp_path):
                readable, pages, err = test_pdf_with_fitz(tmp_path)
                if readable and pages > 0:
                    # Replace original with repaired copy
                    os.replace(str(tmp_path), str(pdf_path))
                    size_after = pdf_path.stat().st_size
                    repair_results[pdf_path_str] = {
                        "status": "repaired",
                        "method": "pikepdf_to_new",
                        "error": "",
                        "pages_after": pages,
                        "size_before": size_before,
                        "size_after": size_after,
                    }
                    stats["pikepdf_new_fixed"] += 1
                    repaired = True
                else:
                    # Clean up tmp
                    if tmp_path.exists():
                        os.remove(str(tmp_path))
            else:
                if tmp_path.exists():
                    os.remove(str(tmp_path))
        
        # ── Strategy 3: fitz garbage-collect save ──
        if not repaired:
            if repair_with_fitz_save(pdf_path):
                readable, pages, err = test_pdf_with_fitz(pdf_path)
                if readable and pages > 0:
                    size_after = pdf_path.stat().st_size
                    repair_results[pdf_path_str] = {
                        "status": "repaired",
                        "method": "fitz_garbage4",
                        "error": "",
                        "pages_after": pages,
                        "size_before": size_before,
                        "size_after": size_after,
                    }
                    stats["fitz_fixed"] += 1
                    repaired = True
        
        # ── UNRECOVERABLE ──
        if not repaired:
            repair_results[pdf_path_str] = {
                "status": "unrecoverable",
                "method": "none",
                "error": error,
                "pages_after": 0,
                "size_before": size_before,
                "size_after": size_before,
            }
            stats["unrecoverable"] += 1
    
    log(f"\nRepair complete:")
    log(f"  pikepdf (in-place):  {stats['pikepdf_fixed']}")
    log(f"  pikepdf (to new):    {stats['pikepdf_new_fixed']}")
    log(f"  fitz garbage-4:      {stats['fitz_fixed']}")
    log(f"  UNRECOVERABLE:       {stats['unrecoverable']}")
    
    return repair_results, stats


# ── Phase 3: UPDATE MANIFEST ───────────────────────────────────────

def update_manifest(rows, repair_results, corrupt, healthy):
    """Add 'repaired' column to manifest CSV."""
    log(f"\n=== PHASE 3: Updating manifest ===")
    
    # Build lookup: pdf_path -> repair status
    repair_status = {}
    for pdf_path_str, info in repair_results.items():
        repair_status[pdf_path_str] = info["status"]
    
    # Also mark healthy ones
    for pdf_path_str in healthy:
        if pdf_path_str not in repair_status:
            repair_status[pdf_path_str] = "healthy"
    
    # Read original fieldnames
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
    
    # Add 'repaired' column if not present
    if "repaired" not in fieldnames:
        fieldnames = list(fieldnames) + ["repaired", "repair_method", "pages", "repair_error"]
    
    # Write updated manifest
    updated = 0
    with open(MANIFEST_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in rows:
            pdf_path = row["pdf_path"]
            row["repaired"] = repair_status.get(pdf_path, "unscanned")
            
            if pdf_path in repair_results:
                info = repair_results[pdf_path]
                row["repair_method"] = info.get("method", "")
                row["pages"] = str(info.get("pages_after", ""))
                row["repair_error"] = info.get("error", "")[:200]
            elif pdf_path in healthy:
                _, pages, _ = healthy[pdf_path]
                row["repair_method"] = "none_needed"
                row["pages"] = str(pages)
                row["repair_error"] = ""
            else:
                row["repair_method"] = ""
                row["pages"] = ""
                row["repair_error"] = ""
            
            writer.writerow(row)
            updated += 1
    
    log(f"Manifest updated: {updated} rows written with 'repaired' column")


# ── Phase 4: WRITE REPORTS ─────────────────────────────────────────

def write_reports(corrupt, repair_results, stats):
    """Write REPAIR_LOG.md and CORRUPT_UNRECOVERABLE.csv."""
    log(f"\n=== PHASE 4: Writing reports ===")
    
    end_time = datetime.now()
    duration = end_time - START_TIME
    
    # ── Unrecoverable CSV ──
    unrecoverable = [(k, v) for k, v in repair_results.items() if v["status"] == "unrecoverable"]
    
    with open(UNRECOVERABLE_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "pdf_path", "size_bytes", "error_message"])
        for pdf_path_str, info in unrecoverable:
            pdf_path = Path(pdf_path_str)
            bundle = "Part1" if "Part 1" in pdf_path_str else ("Part2" if "Part 2" in pdf_path_str else "Other")
            filename = pdf_path.name
            size_bytes = info.get("size_before", 0)
            error = info.get("error", "Unknown")
            writer.writerow([filename, pdf_path_str, size_bytes, error])
    
    log(f"Unrecoverable CSV written: {UNRECOVERABLE_PATH} ({len(unrecoverable)} files)")
    
    # ── Repair Log (Markdown) ──
    total_attempted = len(corrupt)
    total_repaired = stats["pikepdf_fixed"] + stats["pikepdf_new_fixed"] + stats["fitz_fixed"]
    total_unrecoverable = stats["unrecoverable"]
    
    lines = []
    lines.append("# PDF Repair Log — Foodberg Project")
    lines.append("")
    lines.append(f"**Run date:** {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Duration:** {duration}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total corrupt/zero-page PDFs found | {total_attempted} |")
    lines.append(f"| Repaired — pikepdf (in-place) | {stats['pikepdf_fixed']} |")
    lines.append(f"| Repaired — pikepdf (save-to-new) | {stats['pikepdf_new_fixed']} |")
    lines.append(f"| Repaired — fitz garbage-collect | {stats['fitz_fixed']} |")
    lines.append(f"| **Total repaired** | **{total_repaired}** |")
    lines.append(f"| **Unrecoverable** | **{total_unrecoverable}** |")
    lines.append(f"| Repair success rate | {total_repaired/total_attempted*100:.1f}% |")
    lines.append("")
    lines.append("## Repair Methods Used")
    lines.append("")
    lines.append("1. **pikepdf (qpdf engine) in-place** — `pikepdf.open(allow_overwriting_input=True)` — fixes xref table corruption, zlib errors, malformed streams")
    lines.append("2. **pikepdf save-to-new** — open corrupt, save to new file, replace original — for structured corruption that blocks in-place save")
    lines.append("3. **fitz garbage-collect** — `doc.save(garbage=4, deflate=True)` — removes orphan objects, rebuilds cross-reference")
    lines.append("")
    lines.append("## Detailed Results")
    lines.append("")
    
    # Group by repair method
    for method_label, method_key in [
        ("pikepdf (in-place)", "pikepdf_inplace"),
        ("pikepdf (save-to-new)", "pikepdf_to_new"),
        ("fitz garbage-collect", "fitz_garbage4"),
    ]:
        items = [(k, v) for k, v in repair_results.items() if v["method"] == method_key]
        if items:
            lines.append(f"### Repaired via {method_label} ({len(items)} files)")
            lines.append("")
            for pdf_path_str, info in items:
                fname = Path(pdf_path_str).name
                pages = info["pages_after"]
                size_b = info.get("size_before", 0)
                size_a = info.get("size_after", 0)
                delta = size_a - size_b
                lines.append(f"- `{fname}` → {pages} pages (size: {size_b:,} → {size_a:,}, Δ={delta:+,})")
            lines.append("")
    
    # Unrecoverable
    if unrecoverable:
        lines.append(f"### Unrecoverable ({len(unrecoverable)} files)")
        lines.append("")
        lines.append("| File | Size | Error |")
        lines.append("|------|------|-------|")
        for pdf_path_str, info in unrecoverable:
            fname = Path(pdf_path_str).name
            size = info.get("size_before", 0)
            err = info.get("error", "Unknown")[:100]
            lines.append(f"| `{fname}` | {size:,} | {err} |")
        lines.append("")
    
    lines.append("## Repair Details (per-file)")
    lines.append("")
    lines.append("| File | Method | Pages After | Size Before | Size After |")
    lines.append("|------|--------|-------------|-------------|------------|")
    for pdf_path_str, info in sorted(repair_results.items(), key=lambda x: x[1]["status"]):
        fname = Path(pdf_path_str).name
        method = info["method"]
        pages = info["pages_after"]
        size_b = info.get("size_before", 0)
        size_a = info.get("size_after", 0)
        lines.append(f"| `{fname}` | {method} | {pages} | {size_b:,} | {size_a:,} |")
    
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    log(f"Repair log written: {LOG_PATH}")


# ── MAIN ───────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("PDF CORRUPTION SCANNER & REPAIRER — Foodberg Project")
    log("=" * 60)
    
    # Phase 1: Scan
    results, rows, corrupt, healthy = scan_all_pdfs()
    
    if not corrupt:
        log("No corrupt PDFs found! Nothing to repair.")
        # Still update manifest with healthy status
        repair_results = {}
        stats = {"pikepdf_fixed": 0, "pikepdf_new_fixed": 0, "fitz_fixed": 0, "unrecoverable": 0}
        update_manifest(rows, repair_results, corrupt, healthy)
        return
    
    # Phase 2: Repair
    repair_results, stats = repair_corrupt_pdfs(corrupt)
    
    # Phase 3: Update manifest
    update_manifest(rows, repair_results, corrupt, healthy)
    
    # Phase 4: Write reports
    write_reports(corrupt, repair_results, stats)
    
    log("\n" + "=" * 60)
    log("DONE")
    log(f"  Scanned:   {len(results)} PDFs")
    log(f"  Corrupt:   {len(corrupt)}")
    log(f"  Repaired:  {stats['pikepdf_fixed'] + stats['pikepdf_new_fixed'] + stats['fitz_fixed']}")
    log(f"  Unrecov:   {stats['unrecoverable']}")
    log("=" * 60)


if __name__ == "__main__":
    main()