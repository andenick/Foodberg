# Foodberg — Outputs

This directory holds deliverables, exports, and planning artifacts produced by the Foodberg project.

Foodberg is a **live, deployed** historical food-price explorer at [foodberg.org](https://foodberg.org) — a React + FastAPI web app with a 745 MB SQLite database (~1.3M rows) covering USDA NASS history, FAO producer prices, World Bank Pink Sheet, and BLS retail data. The canonical data pipeline is Robin collectors → `rebake_history.py` → Docker image. See the root [`README.md`](../README.md) for architecture, data sources, and setup.

## Directory Structure

### Data/
Tabular data exports from the database and pipeline.

**`WASDE_PSD/`** — USDA PSD supply & demand quantity exports (the 192 MB PSD dataset, acquired into Robin but not yet surfaced in the web UI). Contains:
- Per-commodity CSV + Parquet pairs for each commodity × geography (e.g., `wasde_psd_corn__us.csv`, `wasde_psd_wheat__world.parquet`)
- `data_dictionary.csv` — column definitions
- `PROVENANCE.md` — source attribution and methodology
- `wasde_psd_full.parquet` — full combined dataset

### Generated/
Generated files and exports from the application or pipeline scripts (placeholder; empty in current state).

### PDFs/
Empty — no PDF deliverables exported to Outputs.

### Reports/
Generated reports and analytics (placeholder; empty in current state).

### KB Wishlist folders (`2026.* KB Wishlist*`)
Knowledge-base acquisition wishlists used to plan source and document acquisition for the scholarly PDF track. These are working planning artifacts, not application output.

| Folder | Version | Entries | Categories |
|--------|---------|---------|------------|
| `2026.04.12 KB Wishlist/` | v1 | 370 | Original scope |
| `2026.04.26 KB Wishlist v2/` | v2 | 825 | Expanded |
| `2026.05.10 KB Wishlist v3 NYC/` | v3 | — | NYC-focused pass |
| `2026.06.20 KB Wishlist v4 Global/` | v4 (current) | 1,985 | 105 categories, 27-col schema |

**Acquisition state (per 2026-05-19 reconciliation audit):** 592 entries acquired (~802 PDFs in `Inputs/`), 1,393 not acquired. Document extraction not yet started.

## Notes

- The canonical data store is the production SQLite database baked into the Docker image, **not** anything in `Outputs/`. The PSD exports here are snapshots from the Robin acquisition pipeline.
- Raw inputs live under `Inputs/` (gitignored; ~802 acquired PDFs + downloadable public API data).
- This project has no chef-facing SaaS dashboard, "Reports Center", vendor-comparison tool, menu-engineering workbook, or LaTeX executive/methodology PDFs — earlier versions of this file described a fictional product and have been replaced.