"""
Foodberg PDF Inventory Manifest + Quality Sampler
Reads all three bundles, builds PDF_MANIFEST.csv,
and samples 5 PDFs across bundles for quality assessment.
"""
import csv
import os
import sys
from pathlib import Path

import fitz  # PyMuPDF

PROJECT = Path(__file__).resolve().parent.parent.parent  # Foodberg project root
BUNDLES = {
    "Part1": PROJECT / "Inputs/2026.04.12 Foodberg Pdfs Part 1/2026.04.12 Foodberg Pdfs",
    "Part2": PROJECT / "Inputs/2026.04.12 Foodberg Pdfs Part 2/2026.04.12 Foodberg Pdfs",
    "Cookbook": PROJECT / "Inputs/cookbook_knowledge_base_2026-04-29/cookbooks_final",
}
MANIFEST_PATH = PROJECT / "Technical/HDARP_Processing/PDF_MANIFEST.csv"
SAMPLE_PATH = PROJECT / "Technical/HDARP_Processing/QUALITY_SAMPLER.md"

# ── Step 1: Build manifest ──────────────────────────────────────────
rows = []
for bundle_name, bundle_dir in BUNDLES.items():
    if not bundle_dir.is_dir():
        print(f"WARNING: {bundle_dir} not found")
        continue
    for pdf_path in sorted(bundle_dir.rglob("*.pdf")):
        size = pdf_path.stat().st_size
        parent_name = pdf_path.parent.name if pdf_path.parent != bundle_dir else ""
        rows.append({
            "pdf_path": str(pdf_path),
            "filename": pdf_path.name,
            "size_bytes": size,
            "bundle": bundle_name,
            "subdirectory": parent_name,
        })

# Write CSV
with open(MANIFEST_PATH, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["pdf_path", "filename", "size_bytes", "bundle", "subdirectory"])
    w.writeheader()
    w.writerows(rows)

# Summary
total_pdfs = len(rows)
total_bytes = sum(r["size_bytes"] for r in rows)
by_bundle = {}
for r in rows:
    by_bundle.setdefault(r["bundle"], {"count": 0, "bytes": 0})
    by_bundle[r["bundle"]]["count"] += 1
    by_bundle[r["bundle"]]["bytes"] += r["size_bytes"]

print("=" * 60)
print("PDF_MANIFEST.csv written")
print(f"  Total PDFs: {total_pdfs}")
print(f"  Total size: {total_bytes:,} bytes ({total_bytes / 1e9:.2f} GB)")
for b, s in by_bundle.items():
    print(f"  {b}: {s['count']} PDFs, {s['bytes']:,} bytes ({s['bytes']/1e9:.2f} GB)")
print("=" * 60)

# ── Step 2: Quality sampler (5 PDFs across bundles) ─────────────────
# Pick samples: numeric from Part1, mid-range from Part2, cookbook from Cookbook
sample_keys = [
    # (bundle, filename sample — pick diverse)
    ("Part1", "1.pdf"),       # very first
    ("Part1", "1000.pdf"),    # mid-range numeric
    ("Part2", None),          # pick based on size
    ("Part2", None),          # pick based on size
    ("Cookbook", None),       # pick based on size
]

# Build lookup
lookup = {(r["bundle"], r["filename"]): r for r in rows}

# Pick Part2 and Cookbook samples by different size percentiles
def pick_by_size(rows, bundle, percentile=50):
    subset = sorted([r for r in rows if r["bundle"] == bundle], key=lambda r: r["size_bytes"])
    idx = min(int(len(subset) * percentile / 100.0), len(subset) - 1)
    return subset[idx]["filename"]

sample_keys[2] = ("Part2", pick_by_size(rows, "Part2", 10))
sample_keys[3] = ("Part2", pick_by_size(rows, "Part2", 90))
sample_keys[4] = ("Cookbook", pick_by_size(rows, "Cookbook", 50))

samples = []
for bundle, fname in sample_keys:
    r = lookup.get((bundle, fname))
    if r:
        samples.append(r)
    else:
        print(f"WARNING: sample {bundle}/{fname} not found")

results = []
for row in samples:
    path = row["pdf_path"]
    size_mb = row["size_bytes"] / 1e6
    try:
        doc = fitz.open(path)
        page_count = doc.page_count
        first_text = ""
        total_images = 0
        for pi in range(min(3, page_count)):
            page = doc[pi]
            text = page.get_text()
            if pi == 0:
                first_text = text[:200].replace("\n", " ").strip()
            imgs = page.get_images(full=True)
            total_images += len(imgs)
        
        # Heuristic: born-digital vs scanned
        if len(first_text) > 100:
            doc_type = "born_digital"
        elif len(first_text) > 10:
            doc_type = "mixed"
        else:
            doc_type = "scanned"
        
        doc.close()
        results.append({
            "bundle": row["bundle"],
            "filename": row["filename"],
            "size_mb": round(size_mb, 2),
            "pages": page_count,
            "first_200_chars": first_text,
            "images_first_3_pages": total_images,
            "doc_type": doc_type,
        })
        print(f"  Sampled: {row['bundle']}/{row['filename']} — {page_count}pp, {doc_type}, {total_images} images")
    except Exception as e:
        results.append({
            "bundle": row["bundle"],
            "filename": row["filename"],
            "size_mb": round(size_mb, 2),
            "pages": 0,
            "first_200_chars": f"ERROR: {e}",
            "images_first_3_pages": 0,
            "doc_type": "corrupt",
        })
        print(f"  CORRUPT: {row['bundle']}/{row['filename']} — {e}")

# ── Step 3: Write QUALITY_SAMPLER.md ─────────────────────────────────
lines = []
lines.append("# Foodberg PDF Quality Sampler\n")
lines.append(f"**Date:** 2026-07-04")
lines.append(f"**Sampled:** {len(results)} PDFs across all three bundles\n")
lines.append("## Methodology\n")
lines.append("- PyMuPDF (`fitz`) page count, text extraction, and image detection")
lines.append("- Born-digital heuristic: >100 chars text on first page → born_digital")
lines.append("- Scanned heuristic: <10 chars → scanned; 10–100 → mixed\n")
lines.append("## Samples\n")
lines.append("| Bundle | Filename | Size (MB) | Pages | Type | Images (1-3) | First text (truncated) |")
lines.append("|--------|----------|-----------|-------|------|-------------|------------------------|")
for r in results:
    text_preview = r["first_200_chars"][:100].replace("|", "\\|")
    lines.append(f"| {r['bundle']} | {r['filename']} | {r['size_mb']} | {r['pages']} | {r['doc_type']} | {r['images_first_3_pages']} | {text_preview} |")

lines.append("\n## Observations\n")
born = [r for r in results if r["doc_type"] == "born_digital"]
scanned = [r for r in results if r["doc_type"] == "scanned"]
mixed = [r for r in results if r["doc_type"] == "mixed"]
corrupt = [r for r in results if r["doc_type"] == "corrupt"]
lines.append(f"- Born-digital: {len(born)}")
lines.append(f"- Scanned/image-based: {len(scanned)}")
lines.append(f"- Mixed: {len(mixed)}")
lines.append(f"- Corrupt/unreadable: {len(corrupt)}")
lines.append("\n## Recommendation\n")
if len(scanned) + len(mixed) > 0:
    lines.append("- Scanned/mixed PDFs → HDARP Sraffa 4.0 OCR pipeline")
if len(born) > 0:
    lines.append("- Born-digital PDFs → HDARP (cloud Claude Read-tool) for tables/equations/figures; Sraffa 4.0 body-text extraction on digital pages is instant")
if len(corrupt) > 0:
    lines.append("- Corrupt/zero-page PDFs → quarantine for manual repair or re-acquisition")

with open(SAMPLE_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"\nQUALITY_SAMPLER.md written — {len(results)} samples")
print("Done.")