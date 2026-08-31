# D06: USDA NASS QuickStats (WASDE commodities) — Data Provenance Record

## What this covers
Annual national (and optionally top-15 state) series for the 48 WASDE-tracked
commodities the site serves, for the three statistic categories PRICE RECEIVED,
PRODUCTION, YIELD — the U.S. farm-side backbone of the site's food-price dataset.
Registry family: `usda_nass_wasde` (**optional** — free API key required).

## Source
- **Name**: USDA NASS QuickStats API
- **URL**: https://quickstats.nass.usda.gov/api (data endpoint `api_get`);
  key registration (instant, free): https://quickstats.nass.usda.gov/api
- **License**: public domain (US federal government data)
- **Retrieved**: per-run in `data/raw/nass/*.fetch_meta.json`
- **Format**: JSON

## Construction method
1. `L07_fetch_nass_wasde.py` reads `NASS_API_KEY` from the environment. Without a key it
   prints instructions and exits 3 (the family stays absent and V01 skips it as optional).
2. Per commodity it queries `statisticcat_desc` in (PRICE RECEIVED, PRODUCTION, YIELD)
   with `agg_level_desc=NATIONAL` (add `--states` for STATE detail), writing one JSON per
   commodity to `data/raw/nass/`.
3. `P07_harmonise_nass.py` parses the JSON into `data/final/usda_nass_wasde.csv`
   (one row per numeric observation; `Value` strings parsed with commas stripped and
   publication suppression codes `(D)/(S)/(NA)/(Z)/(H)` dropped, ranges midpointed).

## Transformations applied
`Value` string parsing only (commas, ranges, suppression codes) — values otherwise
verbatim.

## Known issues
- **Key-gated**: unlike every other source in this package, NASS requires a (free,
   instant) API key. The family is therefore `optional` in the registry.
- Coverage varies by commodity: national PRICE RECEIVED reaches back to 1908 for the
   oldest grains; state detail reliably starts 1950; fruit/nut/specialty crops start
   much later.
- Marketing-year vs calendar-year conventions differ by commodity
  (`reference_period_desc` carries the publisher's own period label).

## Validation
V01 validates the family only when `data/final/usda_nass_wasde.csv` exists (≥1,000 rows,
positive values, coverage 1908–2025 at year granularity).
