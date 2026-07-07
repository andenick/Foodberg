# Foodberg Quick Fixes Report

**Date:** 2026-07-04
**Source:** Data Discovery Audit — high-value, low-effort fixes

---

## Fix 1 — ✅ WasdePsd ORM Model Added

**File:** `backend/database/models.py`

Added `WasdePsd` SQLAlchemy class mapping to the `wasde_psd` table (1.98M rows).
Schema matches the actual DB (commodity, country, market_year, attribute, unit, value,
plus commodity_code, country_code, attribute_id, is_aggregate, n_countries,
vintage_month, source, source_url).

Also updated `backend/database/manager.py` to import `WasdePsd`.

---

## Fix 2 — ✅ Mock Data Removed from fao_client.py

**File:** `backend/data_sources/fao_client.py`

Replaced all hardcoded mock data generators (`generate_mock_historical`, fake index values)
with real SQLite queries against `global_prices`. The client now reads:
- FAO Food Price Index data (source=`FAO`, 3,017 rows)
- FAOSTAT producer prices (source=`FAOSTAT`, 167,589 rows)
- FAOSTAT CPI data (source=`FAOSTAT CPI`, 62,836 rows)

Method surface: `get_food_price_index()`, `get_historical_series()`, `get_all_indices()`,
`get_fao_producer_prices()`, `get_fao_cpi()`, `export_to_excel()` — all backed by real data.

---

## Fix 3 — ✅ robin_client.py Already Has `import os`

**File:** `backend/data_sources/robin_client.py`

The file already had `import os` at line 9. No change required.

---

## Fix 4 — ✅ World Bank Country Codes Standardized

**Database:** `data/foodberg.db`

Standardized 8 World Bank country codes from 2-letter to 3-letter ISO:

| Before | After | Rows |
|--------|-------|------|
| 1W | WLD | 319 |
| AR | ARG | 325 |
| AU | AUS | 364 |
| BR | BRA | 364 |
| CA | CAN | 354 |
| CN | CHN | 360 |
| IN | IND | 364 |
| US | USA | 354 |

Zero remaining 2-letter codes in `source='World Bank'` rows.

---

## Fix 5 & 6 — ✅ Alpha Vantage Prefix Stripped

**Database:** `data/foodberg.db`

Removed `"Alpha Vantage - "` prefix from 2,050 `commodity` values:
- `Alpha Vantage - WHEAT` → `WHEAT`
- `Alpha Vantage - CORN` → `CORN`
- `Alpha Vantage - COFFEE` → `COFFEE`
- `Alpha Vantage - COTTON` → `COTTON`
- `Alpha Vantage - SUGAR` → `SUGAR`

**Code:** Updated `get_commodity_price_history()` in `backend/database/manager.py` to match
— removed the now-unnecessary `f'Alpha Vantage - {series}'` label construction.

---

## Validation

```
from database.models import WasdePsd    → models OK
from data_sources.robin_client import * → robin_client OK
from data_sources.fao_client import *   → fao_client OK
```

FAO client smoke-test: overall index = 125.1, trend = decreasing (−1.2%),
historical series from 1990, producer prices and CPI queries all return real data.