# Foodberg Backend Sync Report

**Date:** 2026-07-04
**Source (canonical production):** `Council/Carson/Technical/deploy/foodberg/backend/`
**Target (project local):** `Projects/Foodberg/backend/`
**Handoff reference:** `HANDOFF_20260612_170000.md` — § "Known issues" item 1

## Summary

Synced the project-local backend from the production deploy tree, closing the gap
flagged in the 2026-06-12 handoff. The deploy tree contained ~20 new endpoints (geo,
coverage, NASS, Pink Sheet, CPI, bulk downloads) + a rebake script that were never
back-propagated to the project workspace.

## Files synced

| File | Action | What changed |
|---|---|---|
| `main.py` | **Merged** | Deploy base (730→1372 lines): added geo/coverage/NASS/Pink Sheet/CPI/bulk-download endpoints, Carson telemetry, `_csv_response` helper, expanded Permissions-Policy, 4 new data sources. **Preserved** project's PSD endpoints (`/api/psd/*`, `_psd_conn()`). Added `wasde_psd` to tables_info. |
| `data_sources/worldbank_client.py` | **Replaced** | 197→577 lines. Project had a basic World-Bank stub. Deploy has the full offline local-DB client with 12 methods: `get_geo_indicators`, `get_producer_price_items`, `get_producer_price_series`, `get_state_price_series`, `get_price_coverage`, `get_source_history`, `get_global_indices`, `get_country_cpi_series`, `get_pinksheet_series`, + original `get_commodity_price`, `get_multiple_commodities`, `get_geo_series`. |
| `database/manager.py` | **Patched** | Added `get_commodity_price_history()` method (56 lines) between `get_global_price` and `get_retail_prices`. Powers `/api/prices/history/{commodity}`. |
| `database/rebake_history.py` | **Copied** | New file (394 lines). Maximal food-data rebake script: loads NASS history, FAOSTAT producer/CPI, World Bank Pink Sheet, BLS retail prices from Robin stores → bakes into foodberg.db. |
| `requirements.txt` | **Replaced** | Added `pyarrow>=14.0.0` for Parquet export on `/api/download/{dataset}.parquet`. |
| `data_sources/robin_client.py` | **Patched** | Added `import os` (1 line). |

## New endpoints from deploy synced to project

| Endpoint | Purpose |
|---|---|
| `/api/prices/history/{commodity}` | Real monthly historical price series (Alpha Vantage data) |
| `/api/prices/coverage` | Multi-source per-commodity coverage badges |
| `/api/prices/source/{commodity}?source=` | Per-source series: nass, pinksheet, retail |
| `/api/geo/indicators` | World Bank development indicators |
| `/api/geo/producer/items` | FAOSTAT producer price items by country coverage |
| `/api/geo/producer/{item}` | Per-country producer price series |
| `/api/geo/states/{commodity}` | NASS state-level farm-gate prices |
| `/api/geo/{indicator_code}` | WB indicator per-region series |
| `/api/indices/global` | Pink Sheet + FAO CPI catalog |
| `/api/indices/cpi/{country}` | Per-country FAO food CPI |
| `/api/indices/pinksheet/{series}` | One World Bank Pink Sheet monthly series |
| `/api/wasde/{commodity}.csv` | CSV download of per-commodity WASDE |
| `/api/indices/{category}.csv` | CSV download of composite index |
| `/api/download/datasets` | Catalog of bulk downloadable datasets |
| `/api/download/dictionary.csv` | Data dictionary (all columns, per dataset) |
| `/api/download/{dataset}.csv` | Full CSV export |
| `/api/download/{dataset}.parquet` | Full Parquet export |

## Project-only endpoints preserved

| Endpoint | Purpose |
|---|---|
| `/api/psd/commodities` | List PS&D commodities with coverage |
| `/api/psd/{commodity}/attributes` | Balance-sheet line items |
| `/api/psd/{commodity}/series` | Multi-year supply/demand series |
| `/api/psd/{commodity}/balance-sheet` | Full annual balance sheet |

## Preserved (not overwritten)

- `venv/` — project virtual environment (Python 3.13)
- `data/foodberg.db` — local dev database
- `config/api_keys.json` — API keys
- `.env` / `.env.example` — environment configuration

## Verification

- `venv/Scripts/python.exe -c "import main; print('OK')"` → **OK**
- `WorldBankClient` introspection: all 12 methods importable
- Endpoint count: 41 `@app.get` routes (deploy base + PSD)
- Merged main.py: 1372 lines (was 430 project, 770 deploy)
- Manager: `get_commodity_price_history` present
- `robake_history.py`: imports clean (`import sqlite3`, pathlib, json, csv, datetime)

## Data sources list (now 9 sources in /api/data/sources)

wasde, fred, bls, fao, worldbank, nass_history, faostat, pinksheet, blsap
(project previously had only 5: wasde, fred, bls, fao, worldbank)

## Architecture note

The deploy tree remains canonical for the production Docker image build pipeline.
The project tree is now a faithful local copy for offline dev and future
enhancements. Frontend code lives in `Projects/Foodberg/frontend/` and was
untouched by this sync.