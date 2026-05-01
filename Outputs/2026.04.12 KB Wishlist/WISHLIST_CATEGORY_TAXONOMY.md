# Foodberg KB Wishlist — Category Taxonomy

**Version**: 1.0
**Created**: 2026-04-12
**Total categories**: 14

This taxonomy defines the scope and inclusion/exclusion rules for the Foodberg scholarly wishlist. Every entry in `2026.04.12_Foodberg_Wishlist.csv` is assigned exactly one `Category` and one `Subcategory`.

---

## Scope Rules

**In scope**:
- Works explaining the **historical dynamics** of food commodity prices (macro, micro, sectoral)
- US-centric but with global comparative context (FAO, World Bank, IMF)
- Agricultural economics, food-system policy, commodity market history
- Chef / restaurant economics where it intersects food-cost or inflation analysis
- Methodology docs for the five data sources Foodberg uses (USDA WASDE, FRED, BLS CPI, FAO FPI, World Bank Pink Sheet)

**Out of scope** (exclude):
- Pure cookbooks, recipe collections (unless they contain commodity-price context)
- Nutrition science unconnected to economics
- Food safety / microbiology
- Purely theoretical microeconomics unrelated to food commodities
- Pre-1800 agricultural history (unless foundational, e.g., Mintz on sugar)

---

## 14 Categories

### 1. Agricultural Economics — Foundations
Price theory, supply response, hedging, storage economics, commodity futures.
**Sub**: `price_theory`, `supply_response`, `futures_markets`, `hedging_storage`, `market_structure`

### 2. US Commodity Policy
Farm Bills, USDA support programs, ethanol mandate (RFS), sugar quotas, dairy compacts.
**Sub**: `farm_bills`, `subsidies_supports`, `biofuels_policy`, `sugar_dairy_policy`, `conservation_policy`

### 3. Food Price History (Long-Run)
Pre-1900 baselines, 20th-century inflation, 1973–74 oil/grain shock, 2007–08 spike, 2010–11 Arab Spring prices, 2022 Russia-Ukraine spike.
**Sub**: `pre_1900`, `20c_inflation`, `1970s_shock`, `2008_crisis`, `2011_spike`, `2022_spike`, `secular_trends`

### 4. Cereals & Grains
Wheat, corn, rice, soybeans, sorghum, CBOT futures, weather/yield risk, ethanol-corn nexus.
**Sub**: `wheat`, `corn`, `rice`, `soybeans`, `cbot_futures`, `yield_weather`

### 5. Meat & Livestock
Beef, pork, poultry, packer concentration, feed-cost pass-through, animal welfare regulation.
**Sub**: `beef_cattle`, `pork`, `poultry`, `packer_concentration`, `feed_costs`, `livestock_policy`

### 6. Dairy
Price supports, Federal Milk Marketing Orders, Margin Protection Program, global dairy trade, NZ/EU comparisons.
**Sub**: `us_dairy_policy`, `milk_markets`, `global_dairy`, `cheese_butter`

### 7. Oils & Fats
Palm, soy, canola, sunflower, olive; tropical vs. temperate oil cycles; climate vulnerability.
**Sub**: `palm_oil`, `soy_oil`, `canola_sunflower`, `olive_oil`, `tropical_cycles`

### 8. Sugar & Sweeteners
Cane vs. beet, HFCS substitution, US sugar program, global sugar quotas.
**Sub**: `cane_beet`, `hfcs`, `us_sugar_program`, `global_sugar`

### 9. Produce, Fruits, Vegetables
Seasonality, cold-chain economics, H-2A labor cost pass-through, California water–produce nexus.
**Sub**: `seasonality`, `cold_chain`, `labor_costs`, `specialty_crops`, `water_ag`

### 10. Global Food Systems
Green Revolution, FAO Food Price Index methodology, global food crises, food security, commodity super-cycles.
**Sub**: `green_revolution`, `fao_fpi_methods`, `food_crises`, `food_security`, `super_cycles`

### 11. Trade & Geopolitics
WTO/Doha, NAFTA/USMCA, China trade war, Russia–Ukraine grain corridor, sanctions, export bans.
**Sub**: `wto_doha`, `nafta_usmca`, `china_trade`, `russia_ukraine`, `export_bans`

### 12. Climate, Land & Inputs
Fertilizer prices, drought, climate-yield papers, energy–food nexus, land-use change.
**Sub**: `fertilizer_inputs`, `drought_weather`, `climate_yields`, `energy_food`, `land_use`

### 13. Chef / Restaurant Economics
Menu engineering, food-cost management, vendor relationships, restaurant inflation pass-through, foodservice pricing.
**Sub**: `menu_engineering`, `food_cost_mgmt`, `vendor_procurement`, `inflation_passthrough`, `foodservice_econ`

### 14. Data Source Methodology
WASDE methodology papers, FRED/BLS CPI technical docs, FAO FPI working papers, WB Pink Sheet methodology, historical price series construction.
**Sub**: `wasde_methods`, `cpi_ppi_methods`, `fao_methods`, `wb_methods`, `series_construction`

---

## Priority Rubric

- **CRITICAL**: Foundational / seminal; central to Foodberg's chef-education mission; without it, a core story cannot be told. (~10% of entries)
- **HIGH**: Major contribution; covers one of the 6 food groups in depth or provides key historical context. (~30%)
- **MEDIUM**: Useful reference; strengthens a specific subcategory. (~45%)
- **LOW**: Tangential or duplicative but worth cataloguing for completeness. (~15%)

## Status Values

- `NEEDED` — not yet acquired
- `DOWNLOADED` — PDF/file acquired
- `PARTIAL` — partial acquisition (excerpt, abstract only, paywalled)
- `UNAVAILABLE` — sought but cannot locate

## Type Values

- `BOOK` — monograph
- `ARTICLE` — peer-reviewed journal article
- `REPORT` — institutional / government report
- `WORKING_PAPER` — NBER, IMF, WB, university working paper
- `CHAPTER` — book chapter
- `DATASET_DOC` — methodology / codebook
- `THESIS` — dissertation or thesis
- `GOV_DOC` — primary government document (USDA bulletin, Fed speech, etc.)

## Commodity Tag

One of: `meat`, `dairy`, `cereals`, `oils`, `sugar`, `produce`, `multi`, `none`

Mapped to Foodberg's 6 food groups. Use `multi` for works covering ≥2 groups; `none` for works on policy/methodology/macro.
