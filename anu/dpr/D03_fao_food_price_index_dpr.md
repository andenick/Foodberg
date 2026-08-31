# D03: FAO Food Price Index — Data Provenance Record

## What this covers
FAO's published monthly Food Price Index and its five commodity-group sub-indices
(meat, dairy, cereals, vegetable oils, sugar), base 2014–2016 = 100, 1990-01 → present.
Registry IDs `fao_fpi_overall`, `fao_fpi_meat`, `fao_fpi_dairy`, `fao_fpi_cereals`,
`fao_fpi_oils`, `fao_fpi_sugar`.

## Source
- **Name**: FAO Food Price Index (published series)
- **URL**: https://www.fao.org/worldfoodsituation/foodpricesindex/en/
  (landing page → `food_price_indices_data.csv`; the document-library href carries a
  rotating hash, so L03 scrapes the landing page with a pinned-URL fallback)
- **License**: CC BY 4.0 (FAO)
- **Retrieved**: recorded per-run in `data/raw/fao_fpi/*.fetch_meta.json`
- **Format**: CSV (4 preamble lines, then `Date, Food Price Index, Meat, Dairy, Cereals,
  Oils, Sugar`)

## Construction method
1. `L03_fetch_fao_fpi.py` downloads the CSV (content-checked for the header and the
   1990-01 origin) and writes a fetch-metadata sidecar.
2. `P03_harmonise_fpi.py` skips the preamble, maps the publisher's columns 1:1 onto the
   six registry series, and writes one tidy CSV each (`date` = first of month, `value`).

## Transformations applied
None. **The FAO index is passed through verbatim and is never recomputed.** FAO chains
the index with 2014–2016 trade-share weights that vary by year; a fixed-weight average
cannot reproduce it. The independent fixed-weight recomputation lives under its own
non-FAO name, `foodberg_global_composite` (D07), precisely so the two can be compared.

## Known issues
- The index is revised for recent months as trade weights update; the CSV is the
  publisher's current vintage.
- Base period 2014–2016 = 100 (older literature sometimes quotes 2002–2004 = 100 —
  a different scale, not a data error).

## Validation
V01 checks all six series: presence, positive numeric values, coverage containing
1990-01 → current with 2-month slack.
