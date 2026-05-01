# Foodberg Wishlist — Document Acquisition Hub

**Purpose**: Platform-by-platform tactics for acquiring the 370 items in `2026.04.12_Foodberg_Wishlist.csv`. Modelled on USSR's `DOCUMENT_ACQUISITION_HUB.md`.

---

## Priority of Attack

1. **Free & authoritative first**: USDA ERS, FAO repository, NBER, IMF, World Bank, CRS Reports, archive.org.
2. **Open-access academic**: AgEcon Search, RePEc/EconPapers, SSRN, institutional repositories.
3. **Publisher direct PDFs** (often gated but sometimes free): Science, Nature, PNAS, Oxford Academic, Cambridge Core.
4. **Anna's Archive / Library Genesis**: primarily for books (Cat 13 chef texts, historical volumes, Mintz, Cronon, Cochrane, Gardner).
5. **archive.org**: pre-1980 USDA bulletins, out-of-copyright books, NGO PDFs.
6. **JSTOR / institutional access**: journal back-runs (AJAE, Food Policy, J Farm Econ, J Political Economy).

---

## Platform-Specific Tactics

### USDA ERS (`ers.usda.gov`)
- **Landing page for all reports**: https://www.ers.usda.gov/publications/
- Filter by **Publication Type**: "Outlook", "ERR", "EIB", "TB", "WRS", "AIB", "FDS".
- Outlooks (monthly) are always free PDFs — grab **Wheat, Feed, Rice, Oil Crops, Livestock-Dairy-Poultry, Sugar & Sweeteners, Vegetables & Pulses** at minimum.
- For old ERS reports (pre-2000) not on the main site, check the USDA Economics, Statistics and Market Information System (ESMIS) at Mann Library, Cornell: https://usda.library.cornell.edu/.
- Historical ERS bulletins (1930s–1970s) → archive.org `USDA` collection.

### USDA NASS / AMS / FAS
- NASS Quick Stats: https://quickstats.nass.usda.gov/ (for price series)
- AMS Federal Milk Marketing Order publications: https://www.ams.usda.gov/resources/marketing-order-statistics
- FAS Oilseeds & Livestock World Markets: https://www.fas.usda.gov/data/

### Congressional Research Service (CRS)
- Public portal since 2018: https://crsreports.congress.gov/
- Older CRS reports: https://www.everycrsreport.com/ (archive) and https://fas.org/sgp/crs/
- Search by report number (e.g., `R45525`, `R43325`) — always free, always PDF.

### FAO Documents Repository
- Catalog: https://www.fao.org/documents
- Food Price Index landing: https://www.fao.org/worldfoodsituation/foodpricesindex/
- Flagships always free: **SOFA**, **SOFI**, **Food Outlook** (biannual), **Cereal Supply & Demand Brief** (monthly).

### World Bank
- Commodity Markets Outlook + Pink Sheet: https://www.worldbank.org/en/research/commodity-markets
- Open Knowledge Repository: https://openknowledge.worldbank.org/ (all WB publications, free).
- Policy Research Working Papers: search by WP number (e.g., `4682`, `4333`).

### IMF
- Publications portal: https://www.imf.org/en/Publications
- Working Paper search: https://www.imf.org/en/Publications/WP
- World Economic Outlook commodity chapters are the main target — always free.

### NBER Working Papers
- Search: https://www.nber.org/papers
- Free to download for institutional users; US residents can often get free via `nberpubs.nber.org` mirror or author's homepage.
- Common Foodberg-relevant WP themes: financialization of commodities, ethanol policy, climate-yield.

### IFPRI
- Discussion Papers + Issue Briefs: https://www.ifpri.org/publications
- Always free PDFs.

### AgEcon Search (U Minnesota)
- Open-access archive: https://ageconsearch.umn.edu/
- Holds ~80k ag-econ papers; filter by journal (e.g., *Choices*, *Ag Finance Review*, *J Ag Applied Econ*).
- Use OAI harvesting for bulk: `https://ageconsearch.umn.edu/cgi/oai2`.

### Farm Foundation / Choices Magazine / farmdoc daily
- https://www.farmfoundation.org/
- https://www.choicesmagazine.org/ (AAEA's public-facing magazine — always free)
- https://farmdocdaily.illinois.edu/ (U Illinois — excellent current commentary)

### Federal Reserve Bank Research
- St. Louis FRED: https://fred.stlouisfed.org/ (data + FRED blog posts)
- Kansas City Fed (Ag symposia): https://www.kansascityfed.org/agriculture/
- Chicago Fed: https://www.chicagofed.org/ (AgLetter)
- Philadelphia Fed, Minneapolis Fed also publish food/ag commentary.

### BLS
- CPI methodology: https://www.bls.gov/cpi/additional-resources/
- Handbook of Methods (Chapter 17, CPI): https://www.bls.gov/opub/hom/cpi/
- Monthly Labor Review: https://www.bls.gov/opub/mlr/

### Anna's Archive (books)
- Search URL pattern: `https://annas-archive.org/search?q=<query>`
- Best for: **Category 1 books** (Tomek, Gardner), **Cat 3 history books** (Cronon, Cochrane, Mintz, Federico, Kurlansky), **Cat 13 chef textbooks** (Kasavana, Dopson, Feinstein).
- Verify file integrity: look for PDF with ≥5MB and legible table of contents before committing.
- Respect copyright — these are for research acquisition only.

### Library Genesis
- Mirror rotation: `libgen.rs`, `libgen.is`, `libgen.st`.
- Primary use: older editions of textbooks (Tomek 4th ed, Schmidgall earlier eds).

### archive.org
- Search URL: `https://archive.org/search?query=<query>`
- Exceptional for **pre-1980 USDA bulletins** (collection: `usda_bulletins`, `usdanationalagriculturallibrary`).
- Also holds scanned books out of copyright (pre-1928).

### Google Scholar
- Citation-tree navigation is the killer feature: click "Cited by" to expand snowball.
- For papers with no Direct_URL, use `scholar.google.com/scholar?q=<query>` (already populated in our CSV `Search_Query` + auto-built URLs).
- `scholar.archive.org` as backup when Google Scholar rate-limits.

### JSTOR
- Best for **Journal of Farm Economics** (1919–1967) and early **AJAE** back-runs.
- Many older articles are in JSTOR's Early Journal Content (free).
- Institutional access required for post-paywall items.

### SSRN + RePEc / EconPapers
- SSRN: https://www.ssrn.com/
- RePEc: https://econpapers.repec.org/
- Free for working-paper-stage manuscripts (often identical to published version minus journal formatting).

---

## Workflow — Per Entry

For each row in the CSV:

1. **Try `Direct_URL` first** (when populated).
2. **If no Direct_URL**: hit `Search_Query` on Google Scholar → resolve to a free PDF (author homepage, institutional repo, SSRN).
3. **If still nothing**: try `Anna_Archive_Link` (books) or `Archive_Org_Link` (historical reports, pre-1980 USDA).
4. **Verify** file is correct (title, author, year match) — spot-check TOC & first page.
5. **Update** the CSV: set `Status` to `DOWNLOADED`, move PDF to `Inputs/Literature/<Category>/<slug>.pdf`.
6. **Log** to `RESEARCH_LOG.md` with date, source, any notes.

---

## Bulk Strategies

### USDA Outlooks (monthly)
Write a small scraper against https://www.ers.usda.gov/publications/ filtered by `Publication Type = Outlook` → batch-download all monthly outlooks for the 7 commodity tracks. Single sweep handles ~20 wishlist entries.

### AgEcon Search
Use OAI-PMH harvest (`oai2`) to pull by subject heading (`Agricultural and Food Policy`, `Marketing`). Bulk-grab ~40 entries.

### FAO flagships
Single download-page mirror: `wget -r -l 2 https://www.fao.org/publications/sofa/` (respect robots.txt).

### archive.org
`ia` CLI tool (https://archive.org/developers/internetarchive/cli.html): `ia download --search "USDA wheat situation 1970"`.

---

## Cost

Total expected acquisition cost: **$0** (given USDA/FAO/WB/CRS free, AgEcon Search free, Anna's Archive/Library Genesis for books).

Paywall items where we may need to accept abstract-only or seek ILL:
- JSTOR-only older AJAE/JFE articles (some; many now Early Journal Content)
- Elsevier/Springer journal articles without SSRN pre-print
- ~10–15 entries estimated; mark `Status = PARTIAL` if only abstract obtained.

---

## Quality Gates Before Marking DOWNLOADED

- PDF opens and is searchable (not image-only; if image-only, flag for Sraffa-OCR pipeline)
- Title, author, year on cover page match CSV metadata
- Pages 1–10 legible (no extraction failures)
- Filename follows convention: `FB-<CategoryShort>-<Number>_<AuthorLast>_<YearShort>.pdf`

---

*Maintainer note: as entries move to DOWNLOADED, keep the JSON twin in sync by editing entries in `_generate_wishlist.py` (change `status="NEEDED"` → `"DOWNLOADED"`) and rerunning — this is the single source of truth.*
