# Foodberg Discovery: Robin Food-Data Audit

**Date:** 2026-07-04  
**Auditor:** explore agent (pi)  
**Scope:** All Robin Council food-related data stores under `D:\Arcanum\Council\Robin\DATA\`  
**Method:** Read-only inspection — file listing, column sampling, distinct-value enumeration, cross-reference against `foodberg.db` and `rebake_history.py`

---

## 1. Store-by-Store Inventory

### 1.1 USDA_NASS_HISTORY (1,018 MB, 49 files + MANIFEST)

| Dimension | Detail |
|-----------|--------|
| **Format** | One JSON per commodity, structured as `{commodity, blocks: {national|state/{PRICE RECEIVED, PRODUCTION, YIELD}: {data: [...]}}}` |
| **Commodities** | 46 total. Top-15 (state-level): WHEAT, CORN, SOYBEANS, COTTON, RICE, BARLEY, OATS, SORGHUM, HAY, CATTLE, HOGS, MILK, EGGS, POTATOES, PEANUTS. Plus 31 national-only: almonds, apples, avocados, canola, chickens, cranberries, flaxseed, grapes, honey, lentils, millet, mohair, mushrooms, oranges, peas, pork, rapeseed, rye, safflower, sheep, strawberries, sugarcane, sunflower, sweet potatoes, tobacco, turkeys, walnuts, wool, pecans, pistachios, hazelnuts, blueberries, bison, goats |
| **Categories** | PRICE RECEIVED, PRODUCTION, YIELD |
| **Levels** | NATIONAL (1908–2026), STATE (1950–2026 for top-15) |
| **Frequencies** | Annual + Monthly (PRICE RECEIVED monthly back to 1908 for wheat) |
| **Largest files** | wheat.json (227 MB / 230,846 records), cattle.json (146 MB / 145,056), hay.json (137 MB / 140,038) |
| **Total records** | ~1.06M across all files |
| **In foodberg.db?** | YES — baked as `wasde_data` (1,061,385 rows) via `rebake_history.py` section 1 |
| **Note** | Replaced older snapshot rows from USDA_WASDE for matching categories. Only PRICE RECEIVED/PRODUCTION/YIELD at NATIONAL + STATE loaded; county-level and non-core categories remain from snapshot. |

### 1.2 USDA_PSD (203 MB, 2 files)

| Dimension | Detail |
|-----------|--------|
| **Format** | Single CSV: `psd_alldata.csv` (2,090,921 rows x 12 columns) |
| **Columns** | Commodity_Code, Commodity_Description, Country_Code, Country_Name, Market_Year, Calendar_Year, Month, Attribute_ID, Attribute_Description, Unit_ID, Unit_Description, Value |
| **Commodities** | **63** — grains (12), oilseeds + meals + oils (22), livestock + dairy (9), sugar (2), fruits/nuts (14), fiber/other (4) |
| **Countries** | **214** — global, every continent, including historical entities (USSR, Czechoslovakia, Yugoslavia, Former East/West Germany, Yemen Aden/Sanaa) |
| **Years** | 1960–2026 (Market_Year dimension) |
| **Attributes** | **69** — comprehensive supply/demand balance sheet |
| **Attribute groups** | Supply (Beginning Stocks, Production, Imports), Demand (Domestic Consumption, Food Use, Feed Use, Industrial Use), Trade (Exports, TY Exports, TY Imports), Processing (Crush, Extraction Rate, Milling Rate), Stocks (Ending Stocks, Stocks-to-Use), Livestock (Cow/Sow Beg. Stocks, Cow/Sow Slaughter, Cows in Milk, Milk Production), Area/Yield |
| **Units** | 11: Metric tons (MT), 1000 MT, 1000 HA, 1000 HEAD, KG/HA, MT/HA, PERCENT, RATIO, 1000 60 KG BAGS, 1000 480 lb Bales, 1000 MT CWE |
| **Distinctive value** | The ONLY Robin source with **global, per-country supply/demand balance sheets.** NASS_HISTORY has US-only price/production/yield. PSD has the full identity: Beg.Stocks + Production + Imports = Consumption + Exports + End.Stocks + Loss, for 63 commodities x 214 countries. |
| **In foodberg.db?** | **NOT IN DB.** Deliberately deferred. `rebake_history.py` comment: USDA PSD (quantities) stays in Robin's raw store — acquired but not baked (no current page consumes supply/demand quantities; honest deferral). |

**Full PSD Commodity List (63):**
- **Grains:** Wheat, Corn, Rice, Milled, Barley, Oats, Sorghum, Millet, Mixed Grain, Rye
- **Oilseeds:** Soybean, Soybean (Local), Rapeseed, Sunflowerseed, Cottonseed, Peanut, Copra, Palm Kernel
- **Meals:** Soybean Meal, Soybean Meal (Local), Rapeseed Meal, Sunflowerseed Meal, Cottonseed Meal, Peanut Meal, Copra Meal, Palm Kernel Meal, Fish Meal
- **Oils:** Soybean Oil, Soybean Oil (Local), Rapeseed Oil, Sunflowerseed Oil, Cottonseed Oil, Peanut Oil, Coconut Oil, Palm Oil, Palm Kernel Oil, Olive Oil
- **Livestock/Dairy:** Meat, Beef and Veal, Meat, Swine, Meat, Chicken, Poultry, Meat, Broiler, Dairy, Butter, Dairy, Cheese, Dairy, Milk, Fluid, Dairy, Dry Whole Milk Powder, Dairy, Milk, Nonfat Dry, Animal Numbers, Cattle, Animal Numbers, Swine
- **Sugar:** Sugar, Centrifugal (with Cane Sugar Production, Beet Sugar Production attributes)
- **Fruits/Nuts:** Apples, Fresh, Cherries (Sweet&Sour), Fresh, Coffee, Green, Grapefruit, Fresh, Grapes, Fresh Table, Lemons/Limes, Fresh, Oranges, Fresh, Orange Juice, Peaches & Nectarines, Fresh, Pears, Fresh, Tangerines/Mandarins, Fresh, Almonds, Shelled Basis, Pistachios, Inshell Basis, Walnuts, Inshell Basis
- **Fiber:** Cotton

### 1.3 USDA_WASDE (188 MB, 37 files)

| Dimension | Detail |
|-----------|--------|
| **Format** | One JSON per commodity, dated 2025-10-23 |
| **Origin** | **MISNAMED.** Despite folder name "WASDE," actual data pulled from NASS Quick Stats API (`source_desc: "SURVEY"`), NOT from published USDA WASDE balance-sheet reports. These are NASS survey observations, not WASDE forecasts. |
| **Commodities** | 35 (almonds, apples, barley, blueberries, canola, cattle, chickens, corn, cotton, cranberries, eggs, flaxseed, goats, grapes, hay, hogs, honey, milk, millet, oats, peanuts, peas, potatoes, rice, rye, safflower, sheep, sorghum, soybeans, strawberries, sunflower, tobacco, turkeys, walnuts, wheat) |
| **Categories** | 23 including PRICE RECEIVED, PRODUCTION, YIELD, plus PROGRESS, CONDITION, STOCKS, SALES, AREA HARVESTED, AREA PLANTED, INVENTORY, SLAUGHTERED, HATCHED, PLACEMENTS, USAGE, etc. |
| **Data points** | Wheat: 45,923; Corn: 27,942; Soybeans: 21,936; smaller commodities from 2 (millet, walnuts) to ~8,200 (oats) |
| **In foodberg.db?** | YES — original load was from these files. Rebake then REPLACED PRICE RECEIVED/PRODUCTION/YIELD with NASS_HISTORY full time series. Other 20 categories remain from snapshot. |
| **Verdict** | Redundant with NASS_HISTORY for core time series. Snapshot-only categories add operational metrics but are point-in-time, not time series. |

### 1.4 FAO (256 MB in FAOSTAT_BULK, plus 0.4 MB root)

**FAO Producer Prices** (`Prices_E_All_Data_(Normalized).csv`, 204 MB)
| Dimension | Detail |
|-----------|--------|
| **Items** | 235 commodities — all major food groups from Abaca to Yautia |
| **Elements** | Producer Price (USD/tonne), Producer Price (LCU/tonne), Producer Price (SLC/tonne), Producer Price Index (2014-2016 = 100) |
| **Countries** | 182 |
| **Years** | 1991–2025 (annual) |
| **In DB?** | Only `Producer Price (USD/tonne)` baked (167,589 rows). **LCU, SLC, and PP Index NOT baked.** |

**FAO Food CPI** (`ConsumerPriceIndices_E_All_Data_(Normalized).csv`, 37 MB)
| Dimension | Detail |
|-----------|--------|
| **Items** | Consumer Prices, Food Indices (2015=100) + median, weighted avg, general indices, food price inflation + median, weighted avg |
| **Countries** | 241 (includes regional aggregates: Africa, Americas, Asia, etc.) |
| **Years** | 2000–2025 (monthly) |
| **In DB?** | Only `Item Code 23013` (Consumer Prices, Food Indices 2015=100) baked (62,836 rows). **Food price inflation NOT baked.** |

**FAO Food Price Index** (root-level JSON)
| Dimension | Detail |
|-----------|--------|
| **Content** | Overall FPI + 5 sub-indices: cereals, dairy, meat, oils, sugar |
| **In DB?** | 3,017 rows in `global_prices` source='FAO' + 2,715 in `composite_indices` |

### 1.5 BLS_AP — Average Price Data (52 files, ~0.5 MB)

| Dimension | Detail |
|-----------|--------|
| **Format** | One JSON per retail food item (48 items), monthly price observations |
| **Items** | Flour, rice, spaghetti, bread (white/whole wheat), cookies, cupcakes, ground beef, chuck roast, sirloin, round roast, stew beef, bacon, pork chops, ham (boneless/canned), sausage, whole chicken, chicken breast, tuna, eggs, milk, yogurt, butter, cheddar, processed cheese, ice cream, apples, bananas, oranges, grapefruit, lemons, peaches, potatoes, lettuce, tomatoes, cabbage, celery, carrots, onions, peppers, orange juice, sugar, coffee (ground/instant), peanut butter, potato chips |
| **Years** | 1980–2026 (most series), some end earlier (whole wheat bread 2000, ham canned 1992) |
| **In DB?** | 20,329 rows in `retail_prices` source='BLS AP' |

### 1.6 WORLD_BANK_PINKSHEET (765 KB, 1 file)

| Dimension | Detail |
|-----------|--------|
| **Format** | `CMO-Historical-Data-Monthly.xlsx` with 5 sheets |
| **Food price series** | 46 series: Cocoa, Coffee (2), Tea (4), Coconut oil, Groundnuts, Groundnut oil, Palm oil, Palm kernel oil, Soybeans, Soybean meal, Soybean oil, Rapeseed oil, Sunflower oil, Fish meal, Maize, Rice (4 varieties), Barley, Wheat (2 classes), Banana (2 markets), Orange, Beef, Chicken, Lamb, Sugar (3 markets), Tobacco, Cotton, plus aggregate indices |
| **Years** | 1960M01–2025M01 (monthly nominal USD) |
| **In DB?** | 49,013 rows in `global_prices` source='World Bank Pink Sheet' |

### 1.7 USDA_FoodDataCentral (47 KB, 5 files)

| Dimension | Detail |
|-----------|--------|
| **Content** | Nutritional profiles for 3 foods: cheddar cheese, raw apple, whole wheat bread |
| **Format** | JSON with detailed nutrient data per 100g |
| **In DB?** | NOT IN DB. No nutrition table exists. |
| **Note** | Tiny sample (3 of ~450,000 foods in full FDC). Useful full pull would be ~7,500 Foundation and SR Legacy foods. |

### 1.8 BLS CPI (23 KB)

| Dimension | Detail |
|-----------|--------|
| **Food relevance** | 8+ food CPI subcomponent series in `economic_indicators`: CPI-Food, CPI-Food at Home, CPI-Food Away, CPI-Cereals/Bakery, CPI-Dairy, CPI-Fruits/Vegetables, CPI-Meats/Poultry/Fish/Eggs, CPI-Food and Beverages, PPI-Farm Products, PPI-Finished Goods: Food |
| **In DB?** | 14,640 total rows in `economic_indicators` (food + non-food indicators)

---

## 2. Data Dimensions Matrix

| Store | Price | Quantity | Production | Consumption | Trade | Stocks | CPI | Nutrition | Geography |
|-------|-------|----------|------------|-------------|-------|--------|-----|-----------|-----------|
| **NASS_HISTORY** | $/unit | — | BU/TONS | — | — | (snapshot) | — | — | US only |
| **USDA_PSD** | — | MT | MT | MT | Imports/Exports MT | Beg/End Stocks MT | — | — | **Global 214 countries** |
| **USDA_WASDE** | $/unit | — | varying | — | — | snapshot | — | — | US only |
| **FAO Producer** | USD/t | — | — | — | — | — | — | — | Global 182 countries |
| **FAO CPI** | — | — | — | — | — | — | index | — | Global 241 countries |
| **FAO FPI** | — | — | — | — | — | — | index | — | Global aggregates |
| **BLS AP** | retail $ | — | — | — | — | — | — | — | US only |
| **Pink Sheet** | USD | — | — | — | — | — | — | — | Global markets |
| **BLS CPI** | — | — | — | — | — | — | index | — | US only |
| **USDA FDC** | — | — | — | — | — | — | — | per 100g | US (3 items) |

---

## 3. What's NOT in foodberg.db

### MAJOR GAP: USDA PSD (203 MB, 2.09M rows)
The single largest untapped food data store. Global supply/demand balances for 63 commodities x 214 countries, 1960-2026. This is the "flow of food through the global system" — production to trade to consumption to stocks. NASS already gives US price/production/yield; PSD adds the global dimension and the full balance-sheet logic. **Highest impact-to-effort ratio of any gap.**

### MODERATE GAP: FAO PP Index + LCU price elements
Only `Producer Price (USD/tonne)` baked. The Producer Price Index (2014-2016=100), local currency (LCU), and standardized local currency (SLC) elements exist in the same CSV but were not loaded. PP Index enables real-price analysis.

### MODERATE GAP: FAO Food Price Inflation
The `ConsumerPriceIndices` CSV has 'Food price inflation' (% change) rows — a direct measure of food inflation not loaded. Only the index level was imported.

### MODERATE GAP: USDA FoodDataCentral — full nutrition
Only 3 foods sampled. The full API has thousands of foods with complete nutrient profiles. Relevant for any nutrition/diet dimension of Foodberg.

### MINOR GAP: NASS operational categories
The WASDE snapshot retains 20 categories (CONDITION, PROGRESS, STOCKS, etc.) not in the NASS_HISTORY full pull. These are point-in-time only. Extending the historical pull to include STOCKS would be relatively straightforward.

---

## 4. USDA_PSD Deep Dive

This is USDA Foreign Agricultural Service's Production, Supply and Distribution database — the canonical global agricultural balance sheet. One row = one attribute value for one commodity in one country in one marketing year.

### Balance-Sheet Identity:
```
Beginning Stocks + Production + Imports
  = Domestic Consumption + Exports + Ending Stocks + Loss
```

With sub-flows: Feed Use, Food Use, Crush, Industrial Use, Seed Use.

### Key Attribute Groups:
- **Supply:** Beginning Stocks, Production, Area Harvested, Yield, Imports
- **Demand:** Domestic Consumption, Food Use Dom. Cons., Feed Dom. Consumption, FSI Consumption, Industrial Dom. Cons., Human Dom. Consumption
- **Trade:** Exports, Imports, TY Exports (Trade Year), TY Imports, TY Imp. from U.S.
- **Processing:** Crush, Extraction Rate, Milling Rate
- **Stocks:** Ending Stocks, Stocks-to-Use
- **Livestock:** Cows in Milk, Cow Slaughter, Sow Slaughter, Beef Cows Beg. Stocks, Dairy Cows Beg. Stocks, Sow Beginning Stocks, Cows Milk Production, Total Slaughter

### Commodities of highest analytical value for Foodberg:

**Grains (12):** Wheat, Corn, Rice (Milled), Barley, Oats, Sorghum, Millet, Mixed Grain, Rye  
*World calories foundation — these are what the global food system runs on.*

**Oilseeds + Products (22):** Soybeans, Soybean Meal, Soybean Oil, Rapeseed, Rapeseed Meal, Rapeseed Oil, Sunflowerseed, Sunflowerseed Meal, Sunflowerseed Oil, Palm Oil, Palm Kernel, Cottonseed, Cottonseed Meal, Cottonseed Oil, Peanut, Peanut Meal, Peanut Oil, Copra, Copra Meal, Coconut Oil, Olive Oil, Fish Meal  
*Processing chains — raw seed to meal (feed) + oil (food/industrial).*

**Livestock + Dairy (9):** Beef and Veal, Chicken, Swine, Broiler, Butter, Cheese, Milk Fluid, Dry Whole Milk Powder, Nonfat Dry Milk  
*Animal protein supply — production, consumption, and trade of meat and dairy.*

**Sugar/Sweeteners (2):** Sugar (Centrifugal), Cane Sugar Production, Beet Sugar Production  
*Global sugar supply chain.*

**Fruits/Nuts/Tree Crops (14):** Apples, Cherries, Coffee, Grapefruit, Grapes, Lemons/Limes, Oranges, Orange Juice, Peaches/Nectarines, Pears, Pistachios, Tangerines/Mandarins, Almonds, Walnuts  
*High-value horticultural products with distinct trade patterns.*

**Fiber (1):** Cotton  
*Technically not food but relevant for land competition with food crops.*
---

## 5. WASDE vs. NASS_HISTORY -- Clarification

| Aspect | USDA_WASDE folder | USDA_NASS_HISTORY folder |
|--------|-------------------|--------------------------|
| **Actual data source** | NASS Quick Stats API | NASS Quick Stats API |
| **Temporal** | Single snapshot (2025-10-23) | Full history 1908-2026 |
| **Commodities** | 35 | 46 |
| **Categories** | 23 (broad) | 3 (narrow) |
| **Category depth** | Shallow but wide | Deep but narrow |
| **Distinctive** | Non-time-series categories | Full history for core categories |

**Bottom line:** Despite the name, USDA_WASDE does NOT contain actual WASDE reports (USDA monthly balance-sheet forecasts). It is a one-time NASS Quick Stats pull labeled WASDE Comprehensive. True USDA WASDE report data is NOT in any Robin store. USDA_PSD is closer to WASDE-style balance sheets but uses observed/historical data, not forecasts.

---

## 6. Other Robin Stores Potentially Food-Relevant

| Store | Size | Relevance | Notes |
|-------|------|-----------|-------|
| **HSUS** | 245 MB / 50 files | Historical Statistics of the US | Agricultural production, prices, land use to 1800s |
| **HSUS_NBER** | 19 KB / 2 files | NBER-format version | Same as HSUS |
| **EIA** | 0.3 MB / 10 files | Energy - ethanol/biofuel | Distant relevance |
| **WDI / WorldBank** | 77 + 269 MB | Food production index, undernourishment | Not deeply checked |
| **ClioInfra** | 25 MB / 170 files | Long-run historical global | May have agricultural series |
| **NBER** | 27 MB / 6,340 files | NBER macro-history | May include historical food prices |
| **FRED** | 4.9 GB / 86 files | Massive FRED cache | Broader scope |
| **OECD** | 33 KB / 6 files | Agricultural support estimates | Very small |
| **EUROSTAT** | Small | European agricultural stats | Not deeply checked |
| **MeasuringWorth** | 20 KB | Historical purchasing power | Food share of CPI |
| **Shaikh_Tonak** | 317 MB / 2,239 files | Academic replication | Unlikely food-specific |
---

## 7. Recommendations - Priority Order for Baking

### TIER 1 - Immediate High Value

**1. USDA_PSD -> new supply_demand table (2.09M rows)**
- Largest food data gap. Global supply/demand balances for 63 commodities x 214 countries, 1960-2026.
- Enables: global food balance sheets, trade flow maps, stocks-to-use ratios, self-sufficiency indices.
- Effort: Low. Single clean CSV. ~1 day.

**2. FAO Producer Price Index -> global_prices**
- Enables real (inflation-adjusted) price analysis. PP Index from same CSV as already-loaded USD/tonne.
- Effort: Trivial.

**3. FAO Food Price Inflation -> global_prices**
- Direct food inflation measure per country, more granular than CPI level.
- Effort: Trivial.

### TIER 2 - High Value, Moderate Effort

**4. Full USDA FoodData Central -> new nutrition table**
- Calories per dollar, nutrient density trends, diet cost analysis.
- Effort: Medium. Fresh API pull for ~7,500 Foundation + SR Legacy foods.

**5. WDI Food Indicators -> economic_indicators**
- Food production index, agricultural value added, undernourishment, dietary energy supply.
- Effort: Medium. Identify food-relevant indicators from WDI panel.

### TIER 3 - Nice to Have

**6. NASS_HISTORY - add STOCKS category to historical pull**
- Stocks-to-use ratio is a key food security metric. Currently only in snapshot.
- Effort: Medium.

**7. HSUS Historical Agricultural Statistics**
- Extends US coverage to 1800s. Long-run food system transformation view.
- Effort: High. 50 files, varied formats.
---

## 8. Schema Design Sketch for PSD supply_demand Table



Companion reference table:


Derived metrics enabled:
- Self-sufficiency ratio = Production / Domestic Consumption
- Trade dependency = Imports / Domestic Consumption
- Stocks-to-use = Ending Stocks / Total Use
- Feed share = Feed Use / Domestic Consumption
- Protein feed efficiency = Meat Production / Feed Use
---

## 9. Key Numbers Summary

| Store | Size | Records | In DB? | Data Type | Priority |
|-------|------|---------|--------|-----------|----------|
| NASS_HISTORY | 1,018 MB | 1,061,385 | Full | US price/production/yield history | - |
| **USDA_PSD** | **203 MB** | **2,090,921** | **None** | **Global supply/demand balances** | **#1** |
| USDA_WASDE | 188 MB | replaced | Partial | NASS snapshot (redundant) | - |
| FAO Producer | 204 MB CSV | 167,589 in DB | Partial | USD/tonne only; PP Index + LCU missing | #2 |
| FAO CPI | 37 MB CSV | 62,836 in DB | Partial | Index level only; inflation missing | #3 |
| FAO FPI | 0.4 MB JSON | 3,017 + 2,715 | Full | FAO food price index | - |
| BLS AP | ~0.5 MB | 20,329 | Full | US retail prices | - |
| Pink Sheet | 0.8 MB XLSX | 49,013 | Full | Global commodity prices | - |
| BLS CPI | ~23 KB | ~14,640 | Partial | Food CPI subcomponents | - |
| USDA FDC | 47 KB | 0 | None | Nutrition (3 items only) | #4 |

---

## 10. Discovery Notes

**Naming WARNING:** USDA_WASDE is a misnomer. Its README says WASDE but data is from NASS Quick Stats API (source_desc: SURVEY), not actual WASDE balance-sheet reports. The true USDA WASDE reports (monthly supply/demand forecasts by USDA World Agricultural Outlook Board) are not in any Robin store. This folder should be renamed to USDA_NASS_SNAPSHOT or merged into NASS_HISTORY. USDA_PSD is the actual balance-sheet data source.

**FAO size discrepancy:** AUTHORITATIVE_COUNTS.json (generated 2026-05-19) lists FAO at 0.4 MB / 4 files, but actual size is ~256 MB / 16 files. The FAOSTAT_BULK/ subdirectory (dated 2026-06-12) was added after the count snapshot. Counts should be regenerated or FAOSTAT_BULK split into its own source entry.

**PSD unit caution:** PSD mixes (MT) for metric tons, (1000 MT) for thousands, (1000 HA), (1000 HEAD), (KG/HA), (MT/HA), and (PERCENT). Cross-series arithmetic MUST convert to a common unit first.

**rebake_history.py is well-documented:** The script cleanly states what was loaded and why PSD was deferred. The comment about no current page consuming supply/demand quantities is an explicit invitation to revisit.

**BLS_AP has dead series:** Several series ended before 2026 (whole wheat bread 2000, ham canned 1992, chuck roast 2017, tuna 2017, cabbage 2012, celery 2014, carrots 1997, butter 2012, cheddar 2003, apples 2017, peaches 2021, yogurt 2002, onions 2020). Useful historically but not current.

**foodberg.db post-rebake census:**
- wasde_data: 1,061,385 rows (NASS_HISTORY + WASDE snapshot remnants)
- global_prices: 290,014 rows (FAOSTAT 167,589 + FAOSTAT CPI 62,836 + Pink Sheet 49,013 + WB 5,509 + FAO FPI 3,017 + Alpha Vantage 2,050)
- retail_prices: 20,399 rows (BLS AP 20,329 + USDA 70)
- economic_indicators: 14,640 rows (FRED + BLS CPI subcomponents)
- composite_indices: 2,715 rows (FAO FPI sub-indices)
- market_prices: 0 rows (empty table - schema exists, no data)