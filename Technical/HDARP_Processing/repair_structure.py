"""
Advanced PDF Structure Repair — handles missing xref/trailer/pages-tree
=======================================================================
For the zero-page corrupt PDFs that have intact page objects but 
broken structural scaffolding (xref table, trailer dict, Pages tree).

Two corruption patterns:
  A) "no trailer" — missing xref, startxref, %%EOF (37 files)
  B) "no /Kids array" — broken Pages tree (28 files)

Strategy:
  1. Scan the raw PDF for all object definitions
  2. Classify objects (/Page, /Catalog, /Pages, etc.)
  3. Rebuild xref table
  4. Rebuild Pages tree (find all Page objects, construct /Kids array)
  5. Rebuild Catalog and trailer
  6. Append everything to the file

Usage:
    D:\Arcanum\Projects\Foodberg\backend\venv\Scripts\python.exe repair_structure.py
"""

import csv
import os
import re
import shutil
import struct
from datetime import datetime
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(r"D:\Arcanum\Projects\Foodberg")
MANIFEST_PATH = PROJECT_ROOT / "Technical" / "HDARP_Processing" / "PDF_MANIFEST.csv"
CORRUPT_CSV = PROJECT_ROOT / "Technical" / "HDARP_Processing" / "CORRUPT_UNRECOVERABLE.csv"
STRUCTURAL_LOG = PROJECT_ROOT / "Technical" / "HDARP_Processing" / "STRUCTURAL_REPAIR_LOG.md"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def find_objects(content: bytes) -> list:
    """Find all object definitions in raw PDF bytes.
    Returns list of (obj_num, gen_num, start_offset, end_offset)."""
    objects = []
    pattern = re.compile(rb'(\d+)\s+(\d+)\s+obj\b')
    for m in pattern.finditer(content):
        obj_num = int(m.group(1))
        gen_num = int(m.group(2))
        start = m.start()
        # Find matching endobj
        end = content.find(b'endobj', m.end())
        if end == -1:
            # Look for next obj or end of file
            next_obj = content.find(b' obj', m.end())
            end = next_obj if next_obj != -1 else len(content)
        else:
            end = end + 6  # include 'endobj'
        objects.append((obj_num, gen_num, start, end))
    return objects

def classify_object(content: bytes, start: int, end: int) -> str:
    """Classify an object by its /Type tag."""
    snippet = content[start:min(end, start+500)]
    type_match = re.search(rb'/Type\s*/(\w+)', snippet)
    if type_match:
        return type_match.group(1).decode()
    
    # Check for other important objects
    if b'/Pages' in snippet and b'/Kids' in snippet:
        return "Pages"
    if b'/Root' in snippet or b'/Catalog' in snippet:
        return "Catalog"
    if b'/XObject' in snippet:
        return "XObject"
    if b'/Font' in snippet:
        return "Font"
    if b'/Metadata' in snippet:
        return "Metadata"
    if b'/Outlines' in snippet:
        return "Outlines"
    return "Unknown"

def rebuild_trailer_and_xref(content: bytes, output_path: str) -> bool:
    """Rebuild xref table and trailer for a no-trailer PDF.
    Returns True on success."""
    
    objects = find_objects(content)
    if not objects:
        return False
    
    log(f"    Found {len(objects)} object definitions")
    
    # Classify objects
    page_objs = []
    catalog_obj = None
    pages_obj = None
    
    for obj_num, gen_num, start, end in objects:
        obj_type = classify_object(content, start, end)
        if obj_type == "Page":
            page_objs.append((obj_num, gen_num, start))
        elif obj_type in ("Catalog",):
            catalog_obj = (obj_num, gen_num, start)
        elif obj_type == "Pages":
            pages_obj = (obj_num, gen_num, start)
    
    log(f"    Pages: {len(page_objs)}, Catalog: {catalog_obj is not None}, Pages-tree: {pages_obj is not None}")
    
    # If we have a Catalog, we're in good shape — just need xref+trailer
    # If not, we need to build the whole scaffolding
    
    # Sort objects by offset for xref
    sorted_objs = sorted(objects, key=lambda x: x[2])
    
    # Build xref table
    xref_lines = []
    xref_lines.append(b"xref")
    xref_lines.append(f"0 {len(sorted_objs) + 1}".encode())
    xref_lines.append(f"{0:010d} {65535:05d} f ".encode())
    
    for obj_num, gen_num, offset, _ in sorted_objs:
        xref_lines.append(f"{offset:010d} {gen_num:05d} n ".encode())
    
    xref_table = b"\n".join(xref_lines) + b"\n"
    
    # Determine the root and pages object numbers
    if catalog_obj:
        root_num = catalog_obj[0]
    else:
        root_num = sorted_objs[-1][0] + 1  # Use a new object number
    
    # Find or create Pages object
    if pages_obj:
        pages_num = pages_obj[0]
    elif page_objs:
        # Use an existing object that looks like a Pages node, or create new
        # Check if any "Unknown" object has /Kids and /Count
        pages_num = None
        for obj_num, gen_num, start, _ in sorted_objs:
            snippet = content[start:start+500]
            if b'/Kids' in snippet:
                pages_num = obj_num
                break
        if pages_num is None:
            pages_num = root_num + 1
    
    # Build Pages tree if needed (just a flat list)
    kids_refs = " ".join([f"{num} {gen} R" for num, gen, _ in page_objs])
    pages_dict = f"<< /Type /Pages /Kids [{kids_refs}] /Count {len(page_objs)} >>"
    
    # Build Catalog
    catalog_dict = f"<< /Type /Catalog /Pages {pages_num} 0 R >>"
    
    # Build trailer
    trailer_dict = f"<< /Size {len(sorted_objs) + 1} /Root {root_num} 0 R >>"
    trailer = b"trailer\n" + trailer_dict.encode() + b"\n"
    
    # Compute startxref (where xref table begins relative to end of original content)
    # We append after original content
    startxref_offset = len(content)
    
    footer = (
        xref_table +
        trailer +
        b"startxref\n" +
        f"{startxref_offset}".encode() +
        b"\n%%EOF"
    )
    
    # Write output
    new_content = content + footer
    
    with open(output_path, 'wb') as f:
        f.write(new_content)
    
    return True

def rebuild_pages_tree(content: bytes, output_path: str) -> bool:
    """Repair a PDF with broken Pages tree (no /Kids array).
    Find all Page objects and rebuild the tree."""
    
    objects = find_objects(content)
    if not objects:
        return False
    
    log(f"    Found {len(objects)} object definitions")
    
    # Find all Page objects
    page_refs = []
    catalog_num = None
    pages_num = None
    
    for obj_num, gen_num, start, end in objects:
        obj_type = classify_object(content, start, end)
        if obj_type == "Page":
            page_refs.append(f"{obj_num} {gen_num} R")
        elif obj_type == "Catalog":
            catalog_num = obj_num
            # Find what Pages object it references
            snippet = content[start:end]
            pages_match = re.search(rb'/Pages\s+(\d+)\s+(\d+)\s+R', snippet)
            if pages_match:
                pages_num = int(pages_match.group(1))
        elif obj_type == "Pages":
            pages_num = obj_num
    
    log(f"    Pages: {len(page_refs)}, Catalog obj: {catalog_num}, Pages obj: {pages_num}")
    
    if not page_refs:
        return False
    
    # Build new Pages tree entry
    kids_str = " ".join(page_refs)
    new_pages_dict = f"<< /Type /Pages /Kids [{kids_str}] /Count {len(page_refs)} >>"
    
    # Replace the broken Pages object in the file
    if pages_num is not None:
        # Find the Pages object definition
        pages_pattern = re.compile(rf'{pages_num}\s+0\s+obj\b'.encode())
        pages_match = pages_pattern.search(content)
        
        if pages_match:
            start = pages_match.start()
            end = content.find(b'endobj', pages_match.end())
            if end == -1:
                return False
            
            # Replace the Pages dictionary content
            obj_start = pages_match.end()  # After "NNN 0 obj"
            obj_end = end
            
            new_obj = (
                content[:start] +
                f"{pages_num} 0 obj\n".encode() +
                new_pages_dict.encode() +
                b"\nendobj" +
                content[obj_end + 6:]
            )
            
            with open(output_path, 'wb') as f:
                f.write(new_obj)
            
            return True
    
    return False

def repair_file(path: str) -> str:
    """Attempt to repair a single file. Returns 'repaired', 'drifted', or 'failed'."""
    filename = Path(path).name
    
    with open(path, 'rb') as f:
        content = f.read()
    
    # Determine corruption type
    has_xref = b'xref\n' in content
    has_startxref = b'startxref' in content
    has_eof = b'%%EOF' in content
    has_kids = b'/Kids' in content and b'/Type /Pages' in content
    
    corruption = []
    if not has_xref:
        corruption.append("no_xref")
    if not has_startxref:
        corruption.append("no_startxref")
    if not has_eof:
        corruption.append("no_eof")
    if not has_kids:
        corruption.append("no_kids")
    
    log(f"  {filename}: {', '.join(corruption) if corruption else 'unknown'}")
    
    # Back up original
    backup = path + ".struct_bak"
    shutil.copy2(path, backup)
    
    repaired = False
    try:
        if "no_xref" in corruption or "no_startxref" in corruption or "no_eof" in corruption:
            repaired = rebuild_trailer_and_xref(content, path)
        elif "no_kids" in corruption:
            repaired = rebuild_pages_tree(content, path)
    except Exception as e:
        log(f"    Error during repair: {e}")
        repaired = False
    
    if not repaired:
        # Restore backup
        os.replace(backup, path)
        return "failed"
    
    # Verify with fitz
    import fitz
    try:
        doc = fitz.open(path)
        pages = len(doc)
        doc.close()
        
        if pages > 0:
            log(f"    ✓ Repaired! {pages} pages")
            os.remove(backup)
            return "repaired"
        else:
            log(f"    ✗ Still 0 pages after repair")
            os.replace(backup, path)
            return "failed"
    except Exception as e:
        log(f"    ✗ fitz verification failed: {e}")
        os.replace(backup, path)
        return "failed"

def main():
    log("=" * 60)
    log("ADVANCED STRUCTURAL PDF REPAIR")
    log("=" * 60)
    
    # Load the zero-page corrupt files
    zero_pages = []
    with open(CORRUPT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            msg = row.get("error_message", "")
            if "Failed to open" not in msg:
                zero_pages.append(row["pdf_path"])
    
    log(f"Targeting {len(zero_pages)} structurally corrupt PDFs")
    
    results = {"repaired": 0, "failed": 0}
    repairs = []
    failures = []
    
    for i, path in enumerate(zero_pages):
        if not os.path.exists(path):
            log(f"  [{i+1}/{len(zero_pages)}] SKIP: {Path(path).name} — file not found")
            results["failed"] += 1
            continue
        
        log(f"\n[{i+1}/{len(zero_pages)}] Repairing...")
        outcome = repair_file(path)
        
        if outcome == "repaired":
            results["repaired"] += 1
            repairs.append(path)
        else:
            # Clean up any leftover backup
            backup = path + ".struct_bak"
            if os.path.exists(backup):
                os.remove(backup)
            results["failed"] += 1
            failures.append(path)
    
    # Summary
    log(f"\n{'='*60}")
    log(f"RESULTS: {results['repaired']} repaired, {results['failed']} still broken")
    log(f"{'='*60}")
    
    # Write log
    with open(STRUCTURAL_LOG, "w", encoding="utf-8") as f:
        f.write("# Structural PDF Repair Log\n\n")
        f.write(f"**Run:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"| Metric | Count |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Attempted | {len(zero_pages)} |\n")
        f.write(f"| Repaired | {results['repaired']} |\n")
        f.write(f"| Failed | {results['failed']} |\n\n")
        
        if repairs:
            f.write("## Repaired\n\n")
            for path in repairs:
                f.write(f"- `{Path(path).name}`\n")
        
        if failures:
            f.write(f"\n## Still Broken ({len(failures)})\n\n")
            for path in failures:
                f.write(f"- `{Path(path).name}`\n")
    
    log(f"Log written: {STRUCTURAL_LOG}")

if __name__ == "__main__":
    main()