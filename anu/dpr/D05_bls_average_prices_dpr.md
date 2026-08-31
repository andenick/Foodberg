# D05: BLS Average Prices (retail food) — Data Provenance Record

## What this covers
The 51 monthly U.S. retail average-price series from the BLS Average Price program:
47 U.S.-city-average items (flour, rice, bread, ground beef, bacon, chicken, eggs, milk,
butter, cheese, apples, bananas, lettuce, tomatoes, sugar, coffee, chips, …) plus 4
Census-region tomato series (Northeast / Midwest / South / West).

## Source
- **Name**: BLS Average Price data (APU series), mirrored on FRED
- **URL**: https://fred.stlouisfed.org/graph/fredgraph.csv?id=<APU_ID> (keyless; the
  canonical program page is https://www.bls.gov/cpi/factsheets/average-prices.htm)
- **License**: public domain (US federal government data)
- **Retrieved**: per-run in `data/raw/blsap/*.fetch_meta.json`
- **Format**: CSV (fredgraph.csv)

## Construction method
1. `L06_fetch_blsgap.py` fetches each APU series keylessly from FRED's CSV mirror.
2. `P05_harmonise_retail.py` writes one tidy CSV per item:
   `date, price, unit, area`. Unit and area are taken from series_registry.json (the
   data contract); the area is "U.S. city average" except the four Census-region tomato
   series, which carry their region.

## Transformations applied
Verbatim prices; missing `.` observations dropped, never imputed.

## Known issues
- APU series begin at various dates (1980s–2010s) and some have gaps where the item was
  not priced; the registry records each item's actual observed range.
- Units are heterogeneous by design ($/lb, $/gallon, $/dozen, $/16 oz, …) — never
  aggregate across items without unit normalization.
- The four regional tomato series (APU0100712311…APU0400712311) overlap the national
  tomato series conceptually but are distinct samples; do not double-count them.

## Validation
V01 checks all 51 series: presence, positive numeric prices, coverage containing each
declared range with 2-month slack.
