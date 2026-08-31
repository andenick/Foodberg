# D01: World Bank Pink Sheet — Data Provenance Record

## What this covers
The 71 monthly nominal-USD commodity price series (energy, fertilizers, food, metals,
precious metals, timber) published in the World Bank Commodity Price Data ("The Pink
Sheet"), Monthly Prices sheet — the site's largest global commodity-price family.

## Source
- **Name**: World Bank Commodity Price Data (The Pink Sheet), monthly
- **URL**: https://www.worldbank.org/en/research/commodity-markets (landing page; the
  per-edition XLSX URL rotates — `CMO-Historical-Data-Monthly.xlsx`). L01 scrapes this
  page for the **current** edition. The long-lived "stable" document URL
  (`.../5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx`)
  is used only as a fallback: it serves a **frozen Dec-2024 vintage**, verified 2026-08.
- **License**: CC BY 4.0 (World Bank)
- **Retrieved**: recorded per-run in `data/raw/pinksheet/*.fetch_meta.json`
- **Format**: XLSX, wide layout (one row per month `YYYYMMM`, one column per commodity)

## Construction method
1. `L01_fetch_pinksheet.py` scrapes the landing page for the current edition's href
   (falling back to the frozen pinned URL), downloads it, and writes a fetch-metadata
   sidecar carrying the URL and the publisher's own "Updated on …" banner date.
2. `P01_harmonise_pinksheet.py` locates the names row, units row and the first data row
   dynamically (the sheet layout carries banner rows above the table), then emits one
   tidy CSV per commodity column: `date` (first of month), `value`, `unit` (the
   publisher's own unit token, e.g. `($/mt)`).

## Transformations applied
None on values — verbatim pass-through. Layout only: wide → tidy.

## Known issues
- The monthly sheet publishes **nominal USD only**; no deflated series exists at monthly
  frequency. Any real-terms analysis must use GDPDEF (see D04) at quarterly frequency.
- Columns flagged `**` by the publisher (e.g. "Beef **", "Potassium chloride **") are
  discontinued series: history only, no new observations.
- The publisher prints `0.0` for unquoted months: Thai 25% rice is 0.0 for
  2008-03…2008-06 (Thailand's export ban). These zeros are kept verbatim; V01 warns
  (never fails) on them and fails only on negative values.
- Publication lag: the edition typically appears on the 2nd–3rd business day of the month;
  the newest month(s) may be absent between editions.

## Validation
V01 checks per series (registry IDs `ps_*`): file presence, ≥1 observation, all values
numeric/finite/positive, and actual date coverage containing the declared 1960-01 →
current range with a 2-month slack.
