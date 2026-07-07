# Foodberg WASDE Supply & Demand dataset — provenance

**Built:** 2026-06-21 · **Builder:** `Technical/data_processors/process_psd_wasde.py`

## Source (official, machine-readable)
- **USDA Foreign Agricultural Service — Production, Supply & Distribution (PS&D) database.**
- Bulk CSV downloads: <https://apps.fas.usda.gov/psdonline/downloads/>
  - `psd_grains_pulses_csv.zip`, `psd_oilseeds_csv.zip`, `psd_cotton_csv.zip`,
    `psd_sugar_csv.zip`, `psd_coffee_csv.zip`, `psd_livestock_csv.zip`, `psd_dairy_csv.zip`
  - Downloaded 2026-06-21 to `Inputs/USDA_WASDE_official/psd/` (read-only originals).
- PS&D is the canonical machine-readable supply/demand database underlying the WASDE
  *world* tables. Per USDA FAS it "incorporates all historical revisions" — so the
  headline series here is the **latest vintage** per (commodity, country, marketing year),
  not the as-first-reported value. (For as-first-reported WASDE-report vintages 2010+,
  the consolidated CSV at usda.gov is the alternate source; it was unreachable from the
  build environment — see "Remaining work".)

## What this is / is NOT
- It **is**: USDA FAS PS&D balance sheets (area, yield, production, beginning/ending
  stocks, imports, exports, domestic use, total supply/distribution, stocks-to-use) by
  commodity × country × marketing year, **1960→2026**.
- It is **NOT** a verbatim transcription of the printed WASDE report, and it is **NOT**
  USDA NASS survey data. (The legacy `wasde_data` table is NASS QuickStats *survey* data,
  single-year 2025 — left in place but distinct; it is not this dataset.)
- Season-average farm **prices** are not part of PS&D; the Price Explorer covers prices
  from its own sources (NASS farm-gate, Alpha Vantage spot, BLS retail). This dataset is
  the supply/demand (quantity) side.

## Honesty rules applied (Anu / `.claude/rules/anu-framework.md`)
- **No fabrication, no interpolation.** Missing (commodity, year, attribute) cells are
  simply absent. Non-numeric source values are dropped, never guessed.
- **World aggregate** (`country = "World"`, `is_aggregate = 1`) is a transparent **SUM of
  reported countries** computed ONLY for additive attributes (quantities). It is never
  computed for ratios/percentages/yields (Stocks-to-Use, Yield, Extraction/Milling rate,
  % change, Seed-to-Lint ratio) — those stay per-country only.
- Every row carries `source` and `source_url`.

## Coverage (loaded)
- **50 commodities**, **213 countries (+ World)**, **Market_Year 1960–2026**.
- ~1.94M reported country observations + 38,222 derived World-aggregate rows = **1,981,814 rows**.
- Key commodities with full US + World multi-decade coverage: wheat, corn, rice, barley,
  sorghum, oats, soybean (+ oil, meal), cotton, sugar, coffee, beef, chicken, swine,
  cattle numbers, butter, cheese.

## Files
- `wasde_psd_full.parquet` — the entire long table.
- `wasde_psd_<commodity>__{us,world}.{csv,parquet}` — per (commodity × region) tidy series.
- `data_dictionary.csv` — every (commodity, attribute, unit) with year span and the
  `additive_across_countries` flag.

## Loaded into the app
- Table **`wasde_psd`** in `backend/data/foodberg.db` (indexed on commodity / country /
  market_year / (commodity,country,attribute)).
- Surfaced by the `/api/psd/*` endpoints and the **Supply & Demand** site page.
