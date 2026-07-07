# Foodberg Database Discovery Findings

**Date:** 2026-07-04  
**Database:** backend/data/foodberg.db  
**Size:** 744.04 MB  
**Total Rows:** ~2,451,922 across 8 data tables  

---

## 1. TABLE OVERVIEW

| Table | Rows | Schema Source | Status |
|---|---|---|---|
| wasde_psd | 1,981,814 | Direct CREATE (not in models.py) | Data-rich |
| wasde_data | 442,107 | SQLAlchemy WASDEData | **2025 ONLY** |
| economic_indicators | 14,640 | SQLAlchemy EconomicIndicator | Solid |
| global_prices | 10,576 | SQLAlchemy GlobalPrice | Modest |
| composite_indices | 2,715 | SQLAlchemy CompositeIndex | Derived |
| retail_prices | 70 | SQLAlchemy RetailPrice | **Near-empty** |
| market_prices | 0 | SQLAlchemy MarketPrice | **Empty, broken** |
| data_source_sync | 52 | SQLAlchemy DataSourceSync | Bookkeeping |

---

## 2. TABLE-BY-TABLE DEEP DIVE

### 2.1 wasde_psd -- USDA FAS Production, Supply & Distribution (1,981,814 rows)

**Source:** USDA FAS PSD (loaded as direct SQL CREATE, not in models.py)
**Date Range:** 1960-2026 (market years)  
**Commodities:** 50  
**Countries:** 213  
**Attributes:** 65  

**Top commodities by row count:**

| Commodity | Countries | Attributes | From | To | Rows |
|---|---|---|---|---|---|
| Sugar, Centrifugal | 195 | 16 | 1960 | 2026 | 153,088 |
| Wheat | 146 | 15 | 1960 | 2026 | 117,248 |
| Rice, Milled | 139 | 15 | 1960 | 2026 | 115,111 |
| Corn | 146 | 15 | 1960 | 2026 | 114,728 |
| Cotton | 136 | 12 | 1960 | 2026 | 93,994 |
| Coffee, Green | 95 | 19 | 1960 | 2025 | 87,191 |
| Meal, Soybean | 117 | 14 | 1964 | 2026 | 67,599 |
| Sorghum | 89 | 15 | 1960 | 2026 | 64,913 |
| Barley | 94 | 15 | 1960 | 2026 | 64,073 |
| Oil, Soybean | 110 | 13 | 1964 | 2026 | 62,623 |

**Data Quality:**
- No duplicates (zero duplicate commodity/country/market_year/attribute rows)
- No nulls in any key column (commodity, country, market_year, attribute, value, unit)
- Clean units: only 10 unit types
- 3 thin series (<10 rows): Haiti cattle, Antigua swine, Cyprus butter

**Attributes span the full supply/demand balance:** Beginning Stocks, Production, Imports, Total Supply, Exports, Domestic Consumption, Food/Feed/Industrial Use, Ending Stocks, Yield, Area Harvested, Crush, and sub-variants.

This is the richest table in the database -- 2M rows of global supply/demand data across essentially every major agricultural commodity since 1960.



### 2.2 wasde_data — USDA NASS (442,107 rows) — **CRITICAL: 2025 SNAPSHOT ONLY**

**Date Range:** 2025 only (all rows have year=2025)
**Commodities:** 35 (ALMONDS through WHEAT)
**Aggregation Levels:** NATIONAL, STATE, REGION:MULTI-STATE, COUNTY
**Frequencies:** ANNUAL, MONTHLY, WEEKLY, POINT IN TIME
**73 Statistic Categories**

**Key quality issues:**

| Issue | Count | Detail |
|---|---|---|
| Single-year snapshot | 442,107 | All rows are 2025 only |
| Duplicate rows | Widespread | Up to 375 duplicates per commodity/stat/location/year |
| Null numeric_value | 14,517 | CONDITION and PROGRESS text values not parsed to numbers |
| Zero values | 32,532 | Mostly suppressed county-level data |
| Mixed units | Dozens | Dollar prices mixed with PCT ratings, HEAD counts, ACRES |

**THE REBAKE GAP:** The rebake script at Council/Carson/Technical/deploy/foodberg/backend/database/rebake_history.py was authored (2026-06-12) to load NASS historical data from 45 JSON files at Council/Robin/DATA/USDA_NASS_HISTORY/ — covering PRICE RECEIVED, PRODUCTION, and YIELD from 1908-2026 (national) and 1950-2026 (state, top-15 states) — but it has NOT been executed. Those 45 files contain ~983,000 rows for 43 commodities.

---

### 2.3 economic_indicators — FRED & BLS (14,640 rows)

**Date Range:** 2000-01 to 2026-03
**Distinct Series IDs:** 42 (some duplicated across categories)
**Sources:** FRED (most), BLS

**Food-specific series:**

| Category | Series ID | Description | Range | Rows |
|---|---|---|---|---|
| Food CPI | CUSR0000SAF11 | CPI: Food at Home | 2006-01 to 2026-02 | 241 |
| Food CPI | CUSR0000SEFV | CPI: Food Away from Home | 2006-01 to 2026-02 | 241 |
| Food CPI | CUSR0000SAF111 | CPI: Cereals and Bakery | 2006-01 to 2026-02 | 241 |
| Food CPI | CUSR0000SEFJ | CPI: Dairy | 2006-01 to 2026-02 | 241 |
| Food CPI | CUSR0000SAF112 | CPI: Meats, Poultry, Fish, Eggs | 2006-01 to 2026-02 | 241 |
| Food CPI | CUSR0000SAF113 | CPI: Fruits and Vegetables | 2006-01 to 2026-02 | 241 |
| PPI | WPU01 | PPI: Farm Products | 2006-01 to 2026-02 | 242 |
| PPI | WPU02 | PPI: Processed Foods | 2006-01 to 2026-02 | 242 |
| CPI | CPIUFDSL | CPI: Food | 2015-10 to 2026-02 | 241 |

**Also present (non-food macro):** UNRATE (733), FEDFUNDS (734), GDPC1 (506), SP500 (506), GS10/GS2/GS30 (506 each), M1SL/M2SL (506), CPIAUCSL (615), PCEPI (506), CIVPART (506), HOUST (506), CSUSHPISA (506), VIXCLS (506), EXCSRESNS (506), TOTRESNS (506).

**Data Quality:** No duplicates or nulls. Issues: CPIAUCSL in both CPI and Inflation categories. Most series end mid-2025; only a few reach 2026-03.

---

### 2.4 global_prices — International Prices (10,576 rows)

**Date Range:** 1990-01 to 2026-02
**Commodities:** 27 distinct
**Countries:** 17 (World Bank only)

**By source:**

| Source | Rows | Commodities | Countries | Range |
|---|---|---|---|---|
| Alpha Vantage | 2,050 | 5 (WHEAT, SUGAR, COTTON, CORN, COFFEE) | global | 1992-2026 |
| FAO | 3,017 | 7 Food Price Index sub-indices | global | 1990-2025 |
| World Bank | 5,509 | ~15 indicators | 17 countries (inconsistent codes) | 1990-2024 |

**FAO indices:** Overall, Food, Cereals, Oils, Dairy, Meat, Sugar — monthly since 1990.

**World Bank indicators:** Agriculture Value Added, Cereal Production/Yield, Land Under Cereals, Food/Livestock/Crop Production Indices, Food Imports/Exports (% merchandise), CPI, Undernourishment.

**Data Quality Issues:**
- Alpha Vantage prefix: commodity column stores "Alpha Vantage - WHEAT" instead of using source column
- World Bank country codes: Uses BOTH 2-letter (US, CN) and 3-letter (USA, CHN) codes — separate rows for same countries
- World Bank naming: Near-duplicates like "Agriculture Value Added (% GDP)" vs. "(% of GDP)"

---

### 2.5 retail_prices — Consumer Prices (70 rows) — **NEAR-EMPTY**

**Date Range:** 2025-09-15 (single date)
**Food Items:** 70 distinct — almond, apple, banana, barley, basil, beef-brisket, blueberry, butter, cabbage, canola-oil, carrot, celery, cheese, chicken, chicken-breast, cilantro, cinnamon, cloves, cocoa, coffee, corn, eggs, flour, garlic, ginger, grape, juice, lemon, lettuce, lime, lobster, milk, nutmeg, oats, olive-oil, onion, orange, parsley, pecan, pepper, pistachio, pork, pork-loin, potato, rice, saffron, salmon, salt, shrimp, soybeans, spinach, strawberry, sugar, sugar-white, sunflower-oil, tea, tomato, tomatoes, truffle, tuna, turkey, vanilla, vegetable-oil, walnut, wheat, whey, yeast
**Source:** USDA, National Average, all in lb units.

Single-day snapshot. The rebake script includes BLS Average Prices from 47 JSON files at Council/Robin/DATA/BLS_AP/ — monthly US retail prices for ~50 items from ~1995 to 2026.

---

### 2.6 market_prices — USDA Terminal Market (0 rows) — **EMPTY**

**Rows:** 0
**Schema:** Full (commodity, variety, market_location, low_price, high_price, avg_price, unit, origin, report_date)

The USDA AMS Market News client connects to 12 terminal markets (Atlanta, Boston, Chicago, Columbia, Dallas, Detroit, Los Angeles, Miami, New York, Philadelphia, San Francisco, Seattle) but the import pipeline failed with "attempted relative import beyond top-level package." The data_source_sync entry records FAILED.

---

### 2.7 composite_indices — Computed (2,715 rows)

**Date Range:** 1990-01 to 2025-11
**Categories:** 7 (fao_cereals, fao_dairy, fao_meat, fao_oils, fao_sugar, fao_overall: 431 rows each; bls_overall: 129 rows)
**Base Periods:** 2014-2016 (FAO), 1982-1984 (BLS)

Direct mirrors of FAO Food Price Index and BLS CPI food series — not primary data.

---

### 2.8 data_source_sync — Bookkeeping (52 rows)

Tracks sync status for each collection attempt:
- **WASDE:** 35 individual commodity entries, all SUCCESS, 2026-04-04
- **FRED:** 10 individual series entries, last Oct 2025
- **BLS, FAO, World Bank, Inputs:** Status "NO_DATA" — collection failed or not attempted
- **USDA Market News:** Status "FAILED" with import path error
- **No rebake entries** — rebake was never executed

---

## 3. COMMODITY COVERAGE MATRIX

| Dimension | wasde_psd | wasde_data | economic_indicators | global_prices | retail_prices |
|---|---|---|---|---|---|
| Scope | Global | US only | US macro | Global | US (1-day) |
| Commodities | 50 | 35 | n/a (indices) | 27 | 70 |
| Date range | 1960-2026 | 2025 only | 2000-2026 | 1990-2026 | 2025-09-15 |
| Data type | Supply/demand | Farm prices+prod | CPI/PPI/rates | Price indices+ag stats | Retail snapshot |
| Geography | 213 countries | 4 agg levels | National | 17 countries | National avg |
| Time granularity | Annual | Mixed | Monthly/quarterly | Monthly/annual | Single day |

**Cross-walk of shared commodities (appear in multiple tables):**
- **Wheat, Corn, Rice, Barley, Oats, Sorghum:** In wasde_psd and wasde_data, plus FAO/Alpha Vantage for some
- **Soybeans, Cotton:** In both wasde_psd and wasde_data
- **Milk/Dairy, Beef/Veal, Pork/Swine, Chicken/Poultry:** In wasde_psd; milk/eggs in wasde_data; CPI sub-indices in economic_indicators
- **Sugar:** In wasde_psd and global_prices (Alpha Vantage, FAO index)
- **Coffee:** In wasde_psd and global_prices (Alpha Vantage)
- **Many commodities** (Peanuts, Sunflower, Rapeseed, Palm, Copra, etc.) are ONLY in wasde_psd — no US price data exists for them yet

---

## 4. DATA DIMENSIONS

### Present:

**Quantity dimension (wasde_psd, 1960-2026):**
Production, Area Harvested, Yield, Beginning/Ending Stocks, Exports, Imports, Domestic Consumption, Feed Use, Food Use, Industrial Use, Crush, Total Supply/Distribution/Use, Stocks-to-Use ratio, Animal Numbers — 65 attributes across 50 commodities in 213 countries

**Price dimension:**
- Farm gate: wasde_data PRICE RECEIVED (2025 only, 35 US commodities)
- Index: FAO Food Price Index — 7 sub-indices monthly from 1990
- Macro CPI/PPI: Food at Home, Food Away, Cereals, Meats, Dairy, Fruits/Vegetables, Farm Products, Processed Foods (2006-2026)
- Global spot: 5 commodities via Alpha Vantage (1992-2026)
- Retail: 70 items, single-day snapshot

### Missing:

| Dimension | Where It Lives | Priority |
|---|---|---|
| Historical US farm-gate prices | Robin NASS History (45 files) | IMMEDIATE |
| US retail price time series | Robin BLS AP (47 files) | IMMEDIATE |
| Global producer prices by country | Robin FAOSTAT (204 MB CSV) | IMMEDIATE |
| Monthly spot commodity prices | Robin Pink Sheet | IMMEDIATE |
| Terminal market wholesale prices | USDA AMS API (broken) | HIGH |
| Futures prices | CME/ICE (API needed) | LOW |
| Cost components | USDA ERS, BLS | MEDIUM |
| Organic vs conventional splits | USDA AMS, retail scanner | LOW |
| Regional US retail prices | BLS CPI by MSA | LOW |


---

## 5. REBAKE GAP ANALYSIS

The rebake_history.py script (authored 2026-06-12) loads 5 data sources from Robin. **None have been executed.**

| Re bake Source | Robin Path | Status | Expected Rows |
|---|---|---|---|
| NASS History 1908-2026 | USDA_NASS_HISTORY/ (45 files) | NOT LOADED | ~983,000 |
| FAOSTAT Producer Prices | FAO/FAOSTAT_BULK/Prices.csv (204 MB) | NOT LOADED | Millions available |
| FAOSTAT Food CPI | FAO/FAOSTAT_BULK/CPI.csv (37 MB) | NOT LOADED | Unknown |
| World Bank Pink Sheet | WORLD_BANK_PINKSHEET/CMO.xlsx | NOT LOADED | ~10,000+ |
| BLS Average Prices | BLS_AP/ (47 files) | NOT LOADED | ~10,000+ |

**What the rebake does:**

1. Replaces the 2025-only USDA NASS rows with historical data (1908-2026 national, 1950-2026 state)
2. Adds FAOSTAT producer prices (USD/tonne, annual, per country x item)
3. Adds FAOSTAT consumer food CPI (2015=100, monthly, per country)
4. Adds World Bank Pink Sheet monthly commodity spot prices (60+ series)
5. Adds BLS average retail prices (~50 items, monthly, US city average)

**Impact:** At minimum doubles the row count and adds decades of time-series depth — turning the database from a proof-of-concept into a genuine food price explorer.


---

## 6. DATA QUALITY FLAGS SUMMARY

| Flag | Severity | Table(s) | Detail |
|---|---|---|---|
| wasde_data is 2025-only | CRITICAL | wasde_data | All 442K rows year 2025 |
| market_prices is empty | CRITICAL | market_prices | USDA AMS importer broken |
| retail_prices near-empty | CRITICAL | retail_prices | 70 rows, single date |
| Rebake not executed | CRITICAL | all 5 sources | Script exists but not run |
| WB country codes inconsistent | HIGH | global_prices | 2-letter and 3-letter mixed |
| AV prefix in commodity | HIGH | global_prices | "Alpha Vantage - WHEAT" |
| WB indicator name duplication | MEDIUM | global_prices | "% GDP" vs "% of GDP" |
| Dup series_id across categories | MEDIUM | economic_indicators | CPIAUCSL in CPI and Inflation |
| Stale FRED data | MEDIUM | economic_indicators | Most stop mid-2025 |
| wasde_data duplicate rows | MEDIUM | wasde_data | Up to 375 per combo |
| wasde_data null numeric_value | MEDIUM | wasde_data | 14,517 text-only rows |
| wasde_psd pristine | NONE | wasde_psd | No issues found |


---

## 7. WHAT ROBIN STORES SHOULD BE BAKED NEXT

### Immediate (already scripted — just needs execution):

1. **NASS History** -> wasde_data: 1908-2026 farm-gate prices for 43 commodities. From useless 2025 snapshot to century of time series.

2. **BLS Average Prices** -> retail_prices: ~50 retail food items, monthly, US city average (~1995-2026). Bananas, bread, butter, chicken, coffee, eggs, flour, ground beef, milk, oranges, potatoes, sugar, tomatoes.

3. **FAOSTAT Producer Prices** -> global_prices: Producer-level prices by country x commodity, annual USD/tonne, ~200 countries.

4. **FAOSTAT Consumer Food CPI** -> global_prices: Monthly food CPI per country, 2015=100 index.

5. **World Bank Pink Sheet** -> global_prices: Monthly commodity spot prices for 60+ series (wheat, corn, rice, soybeans, palm oil, sugar, coffee, cocoa). Gold standard for global commodity price analysis.

### Short-term expansions:

6. **Fix USDA Market News importer** -> market_prices: 12-city terminal market prices with high/low/avg by variety, origin, and grade.

7. **FRED/BLS AP refresh** -> economic_indicators: Add 15+ specific retail price series — flour, bread, milk, eggs, bananas, oranges, potatoes, ground beef, steaks, pork chops, chicken breast. Data already in Robin.

### Medium-term:

8. **USDA ERS Food Dollar Series** — farm share, processing, retail, foodservice, energy, transportation breakdown per dollar spent.

9. **FAOSTAT Food Balance Sheets** — per-country supply/utilization accounts.

10. **BLS detailed CPI sub-items** — white bread vs. whole wheat, ground beef vs. steak.


---

## 8. SCHEMA AND CODE ODDITIES

### Schema issues:

- **wasde_psd** (1,981,814 rows, the largest table) is NOT in models.py. Created via raw SQL. Has no ORM mapping.
- **wasde_data.value** is VARCHAR even though numeric_value exists as FLOAT — 14,517 rows have text-only values that were never parsed.
- **global_prices.commodity** conflates real commodity names, index names, and source-prefixed names.
- **market_prices** has full schema with indices but 0 rows — table, indices, and API client all exist, only the import pipeline is broken.

### Code issues:

- **fao_client.py** contains mock data generators with hardcoded fake values — violates the "No Synthetic Data" workspace rule.
- **robin_client.py** is missing "import os" at the top — line references os.environ but os is never imported.
- **Database path ambiguity:** manager.py defaults to parent/data/foodberg.db (744 MB real DB), but there is also a 0-byte stale file at backend/database/foodberg.db.
- **robin_unified_client.py** references ROBIN_DATA_DIR env var defaulting to "Inputs/robin" — should use the actual path or the canonical Robin data structure.


---

## 9. RECOMMENDED IMMEDIATE ACTIONS

1. **Run rebake_history.py.** Single highest-impact action. Loads NASS history (+983K rows), FAOSTAT prices, Pink Sheet commodity spot prices, and BLS retail prices. Expect database to double or triple in row count and gain decades of time-series depth.

2. **Fix the USDA Market News import path.** A single import fix in collect_live.py or usda_client.py would populate market_prices with terminal market data from 12 US cities.

3. **Normalize commodity names in global_prices.** Remove "Alpha Vantage -" prefix. Standardize World Bank country codes to 3-letter. Deduplicate near-identical indicator names.

4. **Remove mock data from fao_client.py.** Replace with real FAOSTAT CSV reader — the data already exists in Robin.

5. **Add wasde_psd to SQLAlchemy models.py** so the ORM can query the richest table.

6. **Map and load BLS AP retail series** into economic_indicators — the 47 JSON files already exist in Council/Robin/DATA/BLS_AP/, they just need to be wired into the collection pipeline.


---

## 10. FILE REFERENCE

| What | Path |
|---|---|
| Database | Projects/Foodberg/backend/data/foodberg.db |
| SQLAlchemy models | Projects/Foodberg/backend/database/models.py |
| Database manager | Projects/Foodberg/backend/database/manager.py |
| Rebake script | Council/Carson/Technical/deploy/foodberg/backend/database/rebake_history.py |
| Robin NASS history | Council/Robin/DATA/USDA_NASS_HISTORY/ (45 files) |
| Robin BLS AP | Council/Robin/DATA/BLS_AP/ (47 files) |
| Robin FAOSTAT | Council/Robin/DATA/FAO/FAOSTAT_BULK/ (2 CSVs, 241 MB) |
| Robin Pink Sheet | Council/Robin/DATA/WORLD_BANK_PINKSHEET/CMO-Historical-Data-Monthly.xlsx |
| USDA AMS client | Projects/Foodberg/backend/data_sources/usda_client.py |
| Robin unified client | Projects/Foodberg/backend/data_sources/robin_unified_client.py |
| Live data collector | Projects/Foodberg/backend/database/collect_live.py |
| Data source clients | Projects/Foodberg/backend/data_sources/ (6 API clients) |
