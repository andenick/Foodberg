# D04: FRED + BLS economic indicators — Data Provenance Record

## What this covers
The 23 macro/food-price context series the site uses: 14 from FRED (fredgraph.csv
keyless mirror) and 9 NSA CUUR CPI series from the BLS public API v1 (keyless). Includes
CPI food aggregates (SA and NSA), CPI food sub-components, PPI farm/processed-foods/wheat,
the federal funds rate, unemployment, and **GDPDEF** — the GDP implicit price deflator,
which is the ONLY series this project permits for nominal→real conversion.

## Source
- **FRED** (14 series: CPIAUCSL, CPIUFDSL, CUSR0000SAF11, CUSR0000SAF111, CUSR0000SAF112,
  CUSR0000SAF113, CUSR0000SEFJ, CUSR0000SEFV, FEDFUNDS, UNRATE, WPU01, WPU02, WPU01130217,
  GDPDEF)
  - **URL**: https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID> (keyless)
  - **License**: public domain (US federal government data)
- **BLS public API v1** (9 series: CUUR0000SAF, CUUR0000SAF11, CUUR0000SAF111,
  CUUR0000SAF112, CUUR0000SAF113, CUUR0000SEFJ, CUUR0000SEFV, CUUR0000SEFV01,
  CUUR0000SEFV02)
  - **URL**: https://api.bls.gov/publicAPI/v1/timeseries/data/ (POST, keyless)
  - **License**: public domain (US federal government data)
- **Retrieved**: per-run in `data/raw/fred/` and `data/raw/bls/` fetch-metadata sidecars
- **Format**: CSV (FRED) / JSON (BLS)

## Construction method
1. `L04_fetch_fred.py` fetches each FRED series as fredgraph.csv (full published
   history; missing values arrive as `.`).
2. `L05_fetch_blsgov.py` POSTs the 9 CUUR series to the BLS v1 API in 10-year windows
   (keyless limit: 25 series/query, 10-year span/query), from 1997 by default (the
   full life of SEFV01/02). Period `M13` (annual average) rows are skipped; only
   calendar months are kept. CUUR0000SEFV01/02 are fetched here because FRED does
   not mirror them.
3. `P04_harmonise_indicators.py` writes one tidy CSV per series:
   `date, value, source` — dropping non-numeric/missing values, never imputing.

## Transformations applied
Verbatim values; windowing/dedup only. Each observation keeps the publisher's own date
(quarter-start for GDPDEF).

## Known issues
- FRED vintage: CPI/PPI series are revised; the CSV is the current vintage (no ALFRED
  realtime handling in this package).
- The BLS windowed fetch defaults to 1997+ (the SEFV01/02 life). Pass `--start <year>`
  to L05 for a shorter or longer CUUR window.
- CUUR0000SEFV01/02 are **Dec 1997 = 100** — a different base than the other CPI series
  (1982–84 = 100). They are context series only: `bls_overall` (D07) is computed solely
  from the five 1982-84-based CUUR components, never from SEFV01/02.

## Validation
V01 checks all 23 series: presence, positive numeric values (all are indices, rates, or
percents > 0), and coverage containing the declared per-series range with 2-month slack.
