# Reproducing Foodberg Data

## Prerequisites
- Python 3.10+
- `pip install -r ../requirements.txt` (requests, openpyxl)

## Execution order

```bash
# Loaders (L##) — one per source, all idempotent (re-runs skip present files)
python L01_fetch_pinksheet.py        # World Bank Pink Sheet XLSX (keyless)
python L02_fetch_faostat.py          # FAOSTAT bulk zips (keyless, ~400 MB; --check to probe)
python L03_fetch_fao_fpi.py          # FAO Food Price Index CSV (keyless)
python L04_fetch_fred.py             # 14 FRED series via fredgraph.csv (keyless)
python L05_fetch_blsgov.py           # 9 BLS CPI series via public API v1 (keyless)
python L06_fetch_blsgap.py           # 51 BLS Average Price series via FRED (keyless)
python L07_fetch_nass_wasde.py       # OPTIONAL: USDA NASS (NASS_API_KEY env; free key)

# Processors (P##) — raw -> data/final/
python P01_harmonise_pinksheet.py    # wide XLSX -> one tidy CSV per commodity
python P02_harmonise_faostat.py      # -> faostat_producer_prices.csv + faostat_food_cpi.csv
python P03_harmonise_fpi.py          # -> 6 fao_fpi_*.csv
python P04_harmonise_indicators.py   # -> 23 indicator CSVs (FRED + BLS)
python P05_harmonise_retail.py       # -> 51 APU retail CSVs
python P06_construct_composites.py   # -> foodberg_global_composite.csv + bls_overall.csv
python P07_harmonise_nass.py         # OPTIONAL: -> usda_nass_wasde.csv (exit 3 if no key)

# Validator (always last)
python V01_validate.py               # exits non-zero on any failure
python V01_validate.py --allow-missing faostat_   # quick run without FAOSTAT
```

## What you get
`data/final/` contains one CSV per series, laid out as:

```
data/final/pink_sheet/ps_<slug>.csv      # date, value, unit
data/final/fpi/fao_fpi_<cat>.csv         # date, value
data/final/indicators/<SERIES_ID>.csv    # date, value, source
data/final/retail/<APU_ID>.csv           # date, price, unit, area
data/final/composites/<name>.csv         # date, value, n_components
data/final/faostat_producer_prices.csv   # long: series_id, country, item, year, date, value
data/final/faostat_food_cpi.csv          # long: series_id, country, item, date, value
data/final/usda_nass_wasde.csv           # long (optional family)
```

Each file matches its `series_registry.json` entry: presence, coverage, units and
sanity are machine-checked by `V01_validate.py`.

## API keys
- **Everything except L07 is keyless.**
- L07 (USDA NASS): free, instant registration at
  https://quickstats.nass.usda.gov/api — then `set NASS_API_KEY=<key>` and re-run.
  Without it the family is simply absent and the validator reports it as SKIP.

## Notes
- All scripts are idempotent: raw files already present are not re-downloaded.
- Every raw artifact in `data/raw/` has a `<file>.fetch_meta.json` sidecar with its
  source URL.
- Provenance details per family: `../dpr/D01`–`D07`.
- Windows: scripts use `pathlib` with package-relative paths only; run them from any
  working directory.
