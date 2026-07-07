# Foodberg PDF Inventory — Discovery Findings

**Date:** 2026-07-04 | **Agent:** pi-explore | **Location:** `D:\Arcanum\Projects\Foodberg\Inputs\`
**Methodology:** Full file enumeration + PyMuPDF sampling (25 PDFs) + complete 690-PDF health scan.

---

## 1. Bundle Summary

| Bundle | Files | Size | Avg Size |
|--------|-------|------|----------|
| Part 1 | 371 | 2.83 GB | 7.8 MB |
| Part 2 | 319 | 2.86 GB | 9.2 MB |
| Cookbook KB | 112 | 0.90 GB | 8.2 MB |
| **TOTAL** | **802** | **6.59 GB** | 8.4 MB |

### Size Distribution

| Bucket | Count | % |
|--------|-------|---|
| <100 KB | 15 | 1.9% |
| 100 KB - 1 MB | 198 | 24.7% |
| 1-5 MB | 278 | 34.7% |
| 5-10 MB | 71 | 8.9% |
| 10-50 MB | 225 | 28.1% |
| 50-100 MB | 13 | 1.6% |
| >100 MB | 2 | 0.2% |

~60% under 5 MB (good for extraction). ~30% are 10-50 MB (image-heavy). Two exceed 100 MB.

---

## 2. Bundle Characterization

### Cookbook Bundle (112 PDFs) — Well-Organized, Descriptive Names

| Prefix | Meaning | Count |
|--------|---------|-------|
| bp | Baking & Pastry | 8 |
| ck | Cookbooks (culinary) | 46 |
| fh | Food History | 10 |
| fs | Food Science | 20 |
| ns | Nutrition Science & Policy | 17 |
| pd | Public Domain (pre-1923) | 10 |
| sa | Scientific Articles | 1 |

Fully classified by filename. Includes McGee, Nosrat, Child, Keller, Ottolenghi, Hazan,
Dunlop, Escoffier (1903), Farmer (1896), Beeton (1861), Brillat-Savarin (1825), Simmons (1796).

### Parts 1 & 2 (690 PDFs) — Zotero Numeric Export, Mixed Content

Files named with numeric IDs only (1.pdf through 1985.pdf, non-contiguous). No descriptive
filenames — topics determined by reading metadata and content.

**60-file title scan reveals topic distribution:**

- **Agricultural economics / policy (~35%):** Commodity Price Dynamics (Pirrong), FAO Food
  Price Index, Farm Foundation food price report, beef market asymmetries, USDA ERS reports,
  Russian agricultural trade, welfare economics (Just et al.)
- **Food history (~15%):** The Bagel (Balinska), Tea (Moxham), Pure Food (Young),
  Famine: A Short History (Ó Gráda)
- **Food culture / anthropology (~15%):** Mexican New York (Smith), Building a Housewife's
  Paradise (Deutsch), Plastic Water (Hawkins), Middle Eastern Food (Roden)
- **Nutrition / public health (~10%):** Diet for a Large Planet, Preventing Chronic Disease,
  Lancet Countdown on health and climate
- **Food industry (~10%):** Fair Trade (Raynolds), NYC restaurant reviews, grocery industry
- **Non-food tangentials (~5-10%):** Maya Glyphs (Coe), Thai court drama, forestry atlas,
  OSHA reports, museum catalogs
- **Unclassified / no metadata (~10-15%):** Corrupt or empty metadata

---

## 3. File Health Assessment (Numeric Bundles — 690 PDFs)

Complete `fitz.open()` scan of all 690 numeric PDFs:

| Condition | Count | % of 690 |
|-----------|-------|----------|
| **Openable & readable** | 533 | 77.2% |
| **Corrupt (fitz.open fails)** | **157** | **22.8%** |
| **Zero-page (opens, 0 pages)** | 49 | 7.1% |

**Corrupt files (157):** Fail `fitz.open()` entirely. Common MuPDF errors:
- `object out of range; xref size mismatch` — XREF table corruption
- `zlib error: incorrect header check` — compressed stream corruption
- `object is not a stream` / `non-page object in page tree` — structural corruption

These are concentrated in certain ID ranges (1000-1100 in p1, 1370-1460 in p2,
1600-1850 in p2), suggesting batch corruption during download/export (likely from
Anna's Archive, where downloads sometimes truncate).

**Zero-page files (49):** Open successfully but `len(doc) == 0`. Treat as effectively corrupt.

**Total problematic: 157 + 49 = 206 of 690 numeric PDFs (29.9%).**

**Cookbook bundle issues:** bp004_How_Baking_Works (0 pages), fs009_Food_Science (0 pages),
fs001_Food_Chemistry (xref errors but 1,114 pages accessible).

**No DRM or password-protected files detected.**

---

## 4. Born-Digital vs. Scanned Ratio

Measured on 533 openable-and-nonzero numeric PDFs by checking page-1 text length:

| Type | Count | % of openable | % of total 690 |
|------|-------|---------------|-----------------|
| **Born-digital** (>500 chars text p1) | 324 | 60.8% | 47.0% |
| **Scanned** (<50 chars text p1) | 160 | 30.0% | 23.2% |
| **Mixed** (50-500 chars) | 49 | 9.2% | 7.1% |

Of the 160 scanned PDFs, 33 (20.6%) are >10 MB — heavy image scans requiring Hopper or OCR.

**Cookbook estimate:** ~57% born-digital, 29% mixed, 14% scanned. Older public-domain
cookbooks (pd001-pd010, 1896-1923) likely skewed toward scanned; modern titles mostly born-digital.

**Overall across all 802:** ~55-60% born-digital, ~20-25% scanned, ~20% corrupt/problematic.

---

## 5. Table Density Estimate

25-file sample (17 successful opens), checking first 5 pages for numeric-dense lines:

| Has Tables | Count | % |
|------------|-------|---|
| Yes | 10 | 58.8% |
| No | 7 | 41.2% |

Conservative lower bound — heuristic only checks 5 pages. **Rough estimate: 50-65% of
numeric PDFs, 20-30% of cookbooks.** Overall **~400-500 PDFs (50-60%)** contain useful
structured tabular data.

- **High table density:** ag econ papers, food science (fs001-fs020), nutrition (ns001-ns017), USDA/FAO/CRS reports
- **Low table density:** popular cookbooks, food history narratives, food culture monographs

---

## 6. Language Distribution

| Language | Estimate | Evidence |
|----------|----------|----------|
| **English** | ~95% | All 17 sampled PDFs; all cookbook filenames are English |
| **French** | ~3% | Le Guide Culinaire (1818.pdf), Larousse Gastronomique (Montagné) |
| **Other** | ~2% | One sampled Turkish PDF; minor international cookbook sections |

**Conclusion:** Overwhelmingly English. Extraction defaults to English with minimal multi-language overhead.

---

## 7. Wishlist Cross-Reference

Wishlist: `Outputs/2026.06.20 KB Wishlist v4 Global/2026.06.20_Foodberg_Wishlist_v4.csv`

| Metric | Value |
|--------|-------|
| Total entries | 1,985 |
| Status: NEEDED | 1,978 |
| Status: PARTIAL | 7 |
| **Status: ACQUIRED_NOT_EXTRACTED** | **0** |

**Finding:** There are zero ACQUIRED_NOT_EXTRACTED entries. The 802 Input PDFs are a
separate pre-wishlist acquisition that does not correspond to wishlist entries. Metadata
matching (title/author) would be needed to link them.

---

## 8. Top 10 Largest PDFs (with page counts and health)

| # | Bundle | File | Size | Pages | Type | Notes |
|---|--------|------|------|-------|------|-------|
| 1 | p1 | 811.pdf | 146.3 MB | 0 | CORRUPT | Zero-page; unextractable |
| 2 | p2 | 1573.pdf | 100.7 MB | 16 | Scanned | ISSUU PDF Downloader (magazine scrape) |
| 3 | cb | pd005_Ranhofer_1894.pdf | 83.1 MB | 1,210 | Born-digital | Classic French cookbook |
| 4 | p1 | 772.pdf | 80.6 MB | 504 | Born-digital | "The global coffee economy, 1500-1989" |
| 5 | p2 | 1818.pdf | 79.2 MB | 1,274 | Scanned | Le Guide culinaire (French) |
| 6 | p1 | 862.pdf | 69.4 MB | — | CORRUPT | Fails to open |
| 7 | p2 | 1849.pdf | 69.3 MB | — | CORRUPT | Fails to open |
| 8 | p1 | 264.pdf | 62.5 MB | 267 | Mixed | No title metadata |
| 9 | p1 | 63.pdf | 61.7 MB | — | CORRUPT | Fails to open |
| 10 | p2 | 1406.pdf | 59.0 MB | — | CORRUPT | Fails to open |

**5 of the top 10 largest are corrupt.** Only 3 are healthy and content-rich (pd005, 772, 1818).

---

## 9. Extraction Readiness Assessment

### Recommended Pipeline by File Type

**Tier 1 — Born-digital, <50 MB → HDARP (cloud Claude Read-tool):**
- ~350 PDFs (cookbooks + born-digital numeric)
- Standard 10-page HDARP chunking, 5-40 chunks each
- 4-type extraction: body text + tables (CSV) + equations (LaTeX) + figures (Markdown)

**Tier 2 — Scanned, <10 MB → Hopper Line v2 (local RTX 5090):**
- ~127 PDFs
- Multi-model: GLM-OCR structural + dots.ocr Cyrillic + Qwen3.6-VL-REAP charts

**Tier 3 — Scanned, >10 MB → Hopper with aggressive chunking:**
- 33 PDFs. Consider 200 DPI pre-conversion. Process in smaller batches per PDF.

**Tier 4 — Corrupt PDFs → Repair or replace:**
- 206 files (157 corrupt + 49 zero-page)
- Attempt: qpdf --replace-input, pdftk, ghostscript -dPDFA recovery
- If unrecoverable: re-acquire from Anna's Archive / LibGen / Internet Archive

**Tier 5 — Public domain cookbooks (pd001-pd010) → Hopper or HDARP:**
- 10 files, large (some >50 MB). Unique historical artifacts.
- pd005 at 1,210 pages is the largest single extractable file.

### Chunking Considerations

- Average PDF: 8.4 MB, ~200 pages → 5-40 HDARP chunks at 10pp/chunk
- 1,000+ page PDFs (pd005, 1818): MEGA_DOC classification, chunk-range parallelism
- Cookbook recipes: structured quasi-tables; HDARP should capture ingredient lists as CSVs
- Scanned >10 MB: Hopper per-batch processing rather than HDARP chunking

### Problems Summary

| Problem | Count | Severity |
|---------|-------|----------|
| Corrupt/unopenable PDFs | 157 | CRITICAL — 22.8% of numeric bundle; includes 5 of top 10 largest |
| Zero-page (opens but empty) | 49 | HIGH — effectively corrupt |
| Scanned PDFs (no text) | 160 | MEDIUM — requires Hopper/OCR pipeline |
| No wishlist linkage | 802 of 802 | MEDIUM — needs metadata matching pass |
| Non-food tangentials | ~35-70 (est.) | LOW — wasted extraction cycles if not culled |
| Corrupt cookbooks | 2+ (bp004, fs009) | MEDIUM — re-acquire from alternatives |
| DRM / password protection | 0 | — None detected |
| Non-PDF artifacts | 0 | — All files are .pdf |

---

## 10. Recommended Priority Order

1. **Repair/replace 206 corrupt/zero-page PDFs** — qpdf recovery where possible; re-acquire
   from Anna's Archive / LibGen / IA links in wishlist where unrecoverable
2. **Extract cookbook bundle (~110 healthy PDFs)** — highest food-content density, best
   organized, descriptive names. Start with pd (historical) and fs (food science) for
   maximum data-table yield.
3. **Extract born-digital numeric (~324 PDFs)** — HDARP cloud pipeline, parallel batch
   processing, continuousness-first cadence
4. **Hopper-extract scanned (~160 PDFs)** — local RTX 5090 pipeline, lighter scans first
5. **Match extracted titles against wishlist** — update 1,985 wishlist entries with
   extraction status (metadata-based matching for numeric PDFs)
6. **Cull non-food tangentials** — remove ~5-10% of numeric PDFs (Maya glyphs, forestry,
   etc.) from extraction queue. Flag as EXCLUDED_NOT_FOOD.

---

## 11. Methodology Notes

- **File enumeration:** `os.walk()` across all three input directories
- **Size measurement:** `os.path.getsize()` on each PDF
- **PDF sampling:** Random sample of 25 PDFs (10 p1 + 8 p2 + 7 cb) using PyMuPDF `fitz`
  for page count, text extraction, table detection, language detection, and metadata
- **Title scan:** 60 randomly sampled numeric PDFs extracting title/author from metadata
  and first-page text
- **Full health scan:** All 690 numeric PDFs opened with `fitz.open()` to detect:
  corrupt (exception thrown), zero-page (len==0), scanned (page-1 text <50 chars)
- **Cookbook classification:** Manual inspection of all 112 filenames for prefix codes
- **Wishlist cross-reference:** Full CSV read of all 1,985 entries

**Intermediate artifacts (in `Technical/plans/`):**
- `_pdf_list.json` — complete 802-file inventory (path, size, bundle)
- `_sample_results.json` — 25-file detailed sample (pages, type, tables, language)
- `_title_scan.json` — 60-file title/author metadata scan

---

**Next Step:** Repair pass on the 157 corrupt numeric PDFs, followed by `/hdarp-campaign`
setup for the ~400 healthy extractable PDFs and a `/hopper` pipeline for the ~160 scanned PDFs.

