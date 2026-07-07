# PDF Repair Log — Foodberg Project

**Run date:** 2026-07-04 22:08–22:15 UTC  
**Tools used:** pikepdf 10.9.1 (qpdf engine), PyMuPDF 1.27.2.3, pypdfium2 5.11.0, pypdf 6.14.2, Ghostscript 10.04.0 (portable extract)

## Summary

| Metric | Count |
|--------|-------|
| Total PDFs in manifest | 802 |
| Healthy (already readable) | 575 |
| **Repaired** | **4** |
| **Unrecoverable** | **223** |
| Repair success rate | 1.8% (4 / 227 corrupt attempted) |

## Repaired Files

| File | Pages | Method |
|------|-------|--------|
| `255.pdf` | 124 | pikepdf in-place (`allow_overwriting_input=True`) |
| `617.pdf` | 1 | pikepdf in-place |
| `828.pdf` | 234 | pikepdf in-place |
| `1829.pdf` | 14 | pikepdf in-place |

## Repair Methods Attempted

### Phase 1: pikepdf (qpdf engine) — ✅ 4 repaired

pikepdf in-place repair (`pikepdf.open(allow_overwriting_input=True)` + `pdf.save()`) fixed 4 files with recoverable xref table corruption.

pikepdf save-to-new and fitz garbage-collect (`garbage=4`) attempted on remaining 223 — all failed.

### Phase 2: Advanced structural reconstruction — ❌ All 65 structural files failed

For the 65 zero-page PDFs (valid headers, intact page objects, but zero renderable pages), multiple approaches were attempted:

| Tool | Approach | Result |
|------|----------|--------|
| Manual xref rebuild | Scan objects, build xref table, add Catalog+Pages tree | fitz still 0 pages |
| Ghostscript 10.04.0 | `-sDEVICE=pdfwrite` on reconstructed file | "Couldn't initialise file" |
| pypdfium2 (PDFium/Chromium) | `PdfDocument(path)` | "Data format error" |
| pypdf (strict=False) | `PdfReader` / `PdfWriter(clone_from=)` | "Stream has ended unexpectedly" |

**Root cause:** Content-stream-level corruption — compressed streams are truncated or malformed at the binary level. Object structure exists but cannot be decompressed. No automated PDF repair tool can reconstruct truncated compressed data.

## Corruption Categories

### DRM-Protected (158 files) — UNRECOVERABLE

158 PDFs use **Adobe ADEPT DRM** (`/Filter/EBX_HANDLER`, `/V 4` encryption). These are ebooks from Adobe Digital Editions (OverDrive, Google Play Books, Kobo, etc.).

**Error:** `unknown encryption handler: 'EBX_HANDLER'`

**Recovery:** Requires the original Adobe Digital Editions activation key. Can be decrypted with DeDRM/NoDRM tools if the ADE key is available from the original machine.

### Structurally Corrupt (65 files) — UNRECOVERABLE

65 PDFs have valid headers (`%PDF-1.x`) and intact page objects but suffer from binary-level stream corruption. All PDF engines (qpdf, MuPDF, PDFium, Ghostscript) fail to open them.

| Subtype | Count | Error |
|---------|-------|-------|
| Broken trailer/xref | 37 | "unable to find trailer dictionary" / "stream ended unexpectedly" |
| Broken Pages tree | 28 | "root of pages tree has no /Kids array" |

**Recovery:** Re-download from original sources. Truncated compressed streams are irrecoverable without the original file.

## Recommendations

1. **DRM files (158):** If Adobe ADEPT key is available, decrypt with DeDRM. Otherwise, unusable.
2. **Structural files (65):** Re-acquire from original sources.
3. **Repaired files (4):** Ready for HDARP processing. Verify page count matches expected.
4. **Healthy files (575):** Ready for HDARP processing.

## Artifacts

- `PDF_MANIFEST.csv` — updated with `repaired`, `repair_method`, `pages`, `repair_error` columns
- `CORRUPT_UNRECOVERABLE.csv` — 223 files with `category` (`DRM_ADEPT` / `STRUCTURAL`) and `recovery_notes`
- `PDF_REPAIR_LOG.md` — this file
- Repair scripts: `repair_corrupt_pdfs.py`, `repair_structure.py` (retained for reference)
- Ghostscript portable: `gs_portable/` (retained for future PDF repair needs)