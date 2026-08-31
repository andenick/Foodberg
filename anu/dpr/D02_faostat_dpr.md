# D02: FAOSTAT bulk downloads — Data Provenance Record

## What this covers
Two FAOSTAT normalized bulk families:
1. **Producer Prices** (`faostat_producer_prices`, registry family): annual producer
   prices in USD/tonne per country × item, 1991→.
2. **Consumer Price Indices: Food** (`faostat_food_cpi`, registry family): monthly
   general food CPI (item 23013, base 2015=100) per country.

## Source
- **Name**: FAOSTAT (Food and Agriculture Organization of the United Nations)
- **URLs**:
  - https://fenixservices.fao.org/faostat/static/bulkdownloads/Prices_E_All_Data_(Normalized).zip
  - https://fenixservices.fao.org/faostat/static/bulkdownloads/ConsumerPriceIndices_E_All_Data_(Normalized).zip
- **License**: CC BY 4.0 (FAO)
- **Retrieved**: recorded per-run in `data/raw/faostat/*.fetch_meta.json`
- **Format**: zip → single large UTF-8-BOM CSV (normalized long layout)

## Construction method
1. `L02_fetch_faostat.py` (`--check` for a HEAD-only size/Last-Modified probe) downloads
   and unzips both bulk files. Each zip is tens of MB and expands to ~200–400 MB.
2. `P02_harmonise_faostat.py` streams the CSVs and filters:
   - Producer prices: `Element == "Producer Price (USD/tonne)"` **and**
     `Months == "Annual value"` → rows keyed `(series_id=PP_<item code>, country, item,
     year)`, date stamped `YYYY-07-01` (mid-year convention, matching the deployed site).
   - Food CPI: `Item Code == 23013` with a real calendar month → rows keyed
     `(series_id=FAO_CPI_FOOD, country, month)`.

## Transformations applied
Row filtering only — values verbatim. Flagged/imputed FAOSTAT codes (`...`, `F`, blank)
are dropped, never guessed.

## Known issues
- The two families ship as one long CSV each (thousands of country × item combinations);
  the registry therefore registers them as **family entries**, validated by row count and
  coverage rather than per-series files.
- Bulk editions lag: the newest calendar year may be partial or absent.
- Sizes: this is the heavyweight step of the package (two ~200 MB+ CSVs). `make quick`
  skips it and runs V01 with `--allow-missing faostat_`.

## Validation
V01 checks each family file: presence, ≥10,000 rows, positive numeric values, and
coverage containing the declared conservative floors (producer prices 1991–2022; food
CPI 2000–2023).
