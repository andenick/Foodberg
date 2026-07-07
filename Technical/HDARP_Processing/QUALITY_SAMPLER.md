# Foodberg PDF Quality Sampler

**Date:** 2026-07-04
**Sampled:** 5 PDFs across all three bundles

## Methodology

- PyMuPDF (`fitz`) page count, text extraction, and image detection
- Born-digital heuristic: >100 chars text on first page → born_digital
- Scanned heuristic: <10 chars → scanned; 10–100 → mixed

## Samples

| Bundle | Filename | Size (MB) | Pages | Type | Images (1-3) | First text (truncated) |
|--------|----------|-----------|-------|------|-------------|------------------------|
| Part1 | 1.pdf | 2.95 | 409 | scanned | 1 |  |
| Part1 | 1000.pdf | 22.06 | 0 | corrupt | 0 | ERROR: Failed to open file 'D:\\Arcanum\\Projects\\Foodberg\\Inputs\\2026.04.12 Foodberg Pdfs Part 1 |
| Part2 | 1701.pdf | 0.37 | 8 | born_digital | 6 | 62  Internasional Journal of Economic, Agribisnis and Development Studies  Vol. 1, No. 2, pp. 62-69, |
| Part2 | 1610.pdf | 23.96 | 78 | born_digital | 318 | www.ruralagrarianstudies.org STATE OF RURAL AND AGRARIAN  INDIA REPORT 2020 Rethinking Productivity  |
| Cookbook | ns011_Fiber_Fueled_Bulsiewicz_2020.pdf | 2.59 | 351 | scanned | 1 |  |

## Observations

- Born-digital: 2
- Scanned/image-based: 2
- Mixed: 0
- Corrupt/unreadable: 1

## Recommendation

- Scanned/mixed PDFs → HDARP Sraffa 4.0 OCR pipeline
- Born-digital PDFs → HDARP (cloud Claude Read-tool) for tables/equations/figures; Sraffa 4.0 body-text extraction on digital pages is instant
- Corrupt/zero-page PDFs → quarantine for manual repair or re-acquisition
