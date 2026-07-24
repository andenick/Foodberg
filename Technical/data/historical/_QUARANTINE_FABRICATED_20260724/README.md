# QUARANTINE — FABRICATED PRICE DATA (2026-07-24)

**Status:** ⛔ **DO NOT IMPORT. DO NOT PUBLISH. DO NOT RE-ENABLE.**
**Authorized by:** user directive 2026-07-24 — *"ofc delete the fake data"*
**Plan reference:** `Technical/plans/FOODBERG_CHEF_FIRST_PLAN_20260724.md` § P0-3
**Executed by:** P0 blocking-work agent, 2026-07-24

---

## What is in here

76 JSON files moved out of `Technical/data/historical/`. Every one of them carries a
**FoodData Central `fdcId`** in its `usdaData` block and presents a year of daily
`price` + `volume` observations attributed to `"source": "USDA"`.

**FoodData Central is a nutrition-composition database. It publishes no prices and no
volumes.** The price and volume fields in these files were generated, not retrieved.

## Evidence of fabrication (not transcription error)

1. **Same `fdcId`, same date, two different prices.** `fdcId 170461` ("Tomato powder")
   appears in both `[2025.09.15] tomato.json` and `[2025.09.15] tomatoes.json`. For
   **2024-09-16** one file states `2.25` and the other `2.14`. A retrieval error cannot
   produce two different values for one identifier on one date; a random generator can.
2. **Every commodity lands in the same narrow band.** All 70 imported "current prices"
   sit between **$2.00 and $3.07 per lb** — saffron ($2.85/lb), truffle ($2.15/lb),
   lobster ($2.71/lb), salt ($2.73/lb) and wheat ($2.19/lb) are all priced within a
   dollar of each other. Real commodity prices span four orders of magnitude.
3. **`volume` is an integer in ~100–1100 with no unit and no meaning.** No USDA endpoint
   emits this field alongside an `fdcId`.
4. **The labels do not match the commodity.** The FoodData Central description was used
   verbatim as the commodity: `tomatoes` → **"Tomato powder"**, `potatoes` →
   **"Bread, potato"**, `oats` → **"Oil, oat"**. A fuzzy name lookup against a nutrition
   database was mistaken for a price feed.

## What was deleted from the database

| Metric | Before | After |
|---|---|---|
| `retail_prices` total rows | **20,429** | **20,359** |
| `retail_prices` where `source='USDA'` (fabricated) | **70** | **0** |
| `retail_prices` where `source='BLS AP'` (real, untouched) | **20,359** | **20,359** |

- **Deleted:** exactly **70** rows, `id` 1–70, all `date = 2025-09-15`,
  `store_type='Retail'`, `location='National Average'`, `quality_grade='Other'`.
- **Predicate:** `DELETE FROM retail_prices WHERE source='USDA'`.
- **Full copy of every deleted row:** `DELETED_ROWS_retail_prices_20260724.csv` (this folder).
- **Machine-readable summary:** `DELETION_MANIFEST.json` (this folder).
- **Database backup taken first:** `backend/data/foodberg.db.backup_20260724_pre_P0-3`
  (1,637,339,136 bytes, byte-identical to the pre-deletion database).

No real data was touched. The 20,359 BLS Average Price rows — the genuine retail series,
including `APU0000712311` tomatoes — are unaffected.

## Why quarantine instead of hard delete

The files are retained so the provenance of *this decision* survives: a future reader can
verify the fabrication claim against the actual artifacts rather than taking it on trust.
They are **not** an archive of usable data.

## Nine files deliberately left in `Technical/data/historical/`

`[2025.09.13] cheese-cheddar.json`, `[2025.09.14] cattle / copper / cotton / feeder /
gasoline / hogs / palladium / platinum.json`.

These are bare `[{date, price, volume}]` arrays with **no metadata block at all** — no
`fdcId`, no `source`, no `commodity`. They contributed **zero rows** to the database (the
importer reads `data.get("historicalData")`, which these files do not have), so they are
outside the authorized deletion. They carry the same `volume` signature as the fabricated
set and **should be treated as unverified**: do not import them without establishing real
provenance first. Flagged here rather than moved, to keep the deletion scope exact.

## Upstream copies that still exist (NOT cleaned by this action)

The same generated payloads exist elsewhere and would re-poison the database if imported:

- `Council/Robin/DATA/OTHER_APIS/USDA_FOOD/data/historical/` — the *upstream* source the
  importer actually points at (`ROBIN_DATA_DIR`). Outside this project's tree; flagged for
  Robin's owner.
- `Projects/Foodberg/Inputs/[2025.09.25] *_2025-09-25.json` — a second, later generation of
  the same payloads (~71 files).

## The import vector

`backend/database/importers/historical_importer.py` is the code that loaded these rows.
It is currently **non-functional anyway** — line 29 calls `os.environ.get(...)` while the
module never imports `os`, so the module raises `NameError` on import. Do not "fix" it
back into service. If a real USDA retail price feed is ever wired up, it must be a new
importer with a documented publisher series ID and retrieval URL per the reality-audit
contract (`Technical/scripts/reality_audit.py`).
