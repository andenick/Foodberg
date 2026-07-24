# Foodberg - Complete Project Index

## Purpose

Historical Food Price Explorer — a data visualization app for understanding food commodity prices and their history. Built for historically minded chefs who want to understand the broader environmental and historical context of food prices. **🟢 LIVE at [foodberg.org](https://foodberg.org).**

**Current status (2026-07-17):** web application active/live; 895 Hopper-read documents landed
and KBIP-catalogued on 2026-07-16; canonical KB integration and RobertDB build still pending.
For chronology, use the [generated project timeline](../../Council/Druck/Technical/History/views/PROJECT_TIMELINE_INDEX.md)
and [workspace timeline](../../Council/Druck/Technical/History/views/WORKSPACE_TIMELINE.md).

## Quick Start

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python -m database.import_all  # Populate database (first time only)
python main.py                 # Starts on http://localhost:8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev                    # Starts on http://localhost:3000
```

### Access Points

- **Production**: https://foodberg.org
- **Local frontend**: http://localhost:3000
- **Local backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (dev mode only)

## Project Structure

```
Foodberg/
  backend/              # FastAPI server (Python) — lags deploy tree
    main.py             # API endpoints
    database/           # SQLAlchemy models, importers, manager
    indices/            # Composite index computation
    data/               # SQLite database (foodberg.db)
    data_sources/       # API clients (FRED, FAO, World Bank, USDA, Robin)
    config/             # API key configuration
  frontend/             # React app (TypeScript) — canonical source
    src/pages/          # 9 pages
    src/services/       # API client (api.ts, defaults to same-origin)
    src/components/     # Header, Footer, ChartDetails
  Inputs/               # Raw data & ~802 acquired PDFs
  Technical/            # Processing scripts, docs, progress log
  Outputs/              # Deliverables (wishlists, PSD exports)
```

> **Deploy tree (canonical production backend):** `Council/Carson/Technical/deploy/foodberg/backend/` — main.py, worldbank_client.py, rebake_history.py, and the baked `data/foodberg.db` live here. The project-local `backend/` lags this tree. Frontend source at `Projects/Foodberg/frontend/` is canonical for both local dev and production builds.

## Frontend Pages

| Route | Page | Data Source |
|-------|------|-------------|
| `/` | HomePage | Static content |
| `/index` | FoodPriceIndex | `GET /api/indices/`, `GET /api/indices/{category}` |
| `/explore` | PriceExplorer | `GET /api/prices/coverage`, `GET /api/prices/history/{commodity}?source=` (tabs: NASS, Pink Sheet, BLS retail) |
| `/commodity/:id` | CommodityDetail | `GET /api/prices/history/{id}` |
| `/geographic` | GeographicPrices | Three-mode toggle: `GET /api/geo/producer/{item}` (FAOSTAT), `GET /api/geo/states/{commodity}` (US NASS), `GET /api/geo/{code}` (WB indicators) |
| `/trends` | HistoricalTrends | `GET /api/prices/history/` (parallel); eligibility restricted to commodities with real history |
| `/sources` | DataSources | `GET /api/data/sources`, `GET /api/data/status` — DB overview + per-source record cards |
| `/downloads` | Downloads | Static content (data exports) |
| `/supply-demand` | SupplyDemand | (placeholder; PSD data acquired, not surfaced) |

## API Endpoints

### Core
- `GET /` — API root (name, version, status)
- `GET /api/health` — Health check
- `GET /api/data/status` — Per-table record counts, date ranges, freshness
- `GET /api/data/sources` — Static source metadata

### Price Explorer (multi-source)
- `GET /api/prices/coverage` — Per-commodity multi-source coverage spans
- `GET /api/prices/history/{commodity}?source=nass|av|pinksheet|retail` — Price history filtered by source
- `GET /api/prices/trend/{commodity}` — Price trend with period filter
- `GET /api/prices/compare/{commodity}` — Cross-source comparison
- `GET /api/prices/stats/{commodity}` — Price statistics
- `GET /api/prices/database/stats` — Database record counts

### Geographic (three-mode)
- `GET /api/geo/producer/items` — List FAOSTAT producer price items
- `GET /api/geo/producer/{item}` — FAOSTAT producer prices by country
- `GET /api/geo/states/{commodity}` — NASS state-level prices
- `GET /api/geo/indicators` — List World Bank indicators
- `GET /api/geo/{code}` — World Bank development indicator data

### WASDE Commodities (legacy, from database)
- `GET /api/wasde/commodities` — List available commodities
- `GET /api/wasde/{commodity}` — All records (params: `limit`)
- `GET /api/wasde/{commodity}/national` — National-level data
- `GET /api/wasde/{commodity}/state/{state}` — State-level data

### Economic Indicators
- `GET /api/economic/indicators` — FRED indicators

### Global Data
- `GET /api/global/fao-index` — FAO Food Price Index
- `GET /api/global/worldbank/{commodity}` — Single commodity
- `GET /api/global/worldbank/multiple` — Multiple commodities

### Composite Indices
- `GET /api/indices/` — Latest values for all categories
- `GET /api/indices/{category}` — Historical values for a category

## Database

The counts below are a historical project-local snapshot. Production is rebuilt from Robin data,
and its exact table counts should be read from the current deploy database rather than inferred
from this index.

SQLite database at `backend/data/foodberg.db` with 6 tables:

| Table | Records | Source |
|-------|---------|--------|
| `wasde_data` | ~1.06M | Robin/USDA NASS (44 commodities, 1908–2026, national + state) |
| `global_prices` | ~220K | FAO FAOSTAT producer prices + FAO CPI + World Bank Pink Sheet CMO |
| `retail_prices` | ~20K | BLS AP monthly averages (1980–2026) via FRED mirror |
| `economic_indicators` | ~13K | FRED (21 series) + BLS CPI (7 series) |
| `composite_indices` | ~3K | Computed from FAO + BLS data |
| `market_prices` | 0 | USDA Market News (not populated) |
| **Total** | **~1.3M** | |

> USDA PSD (192 MB CSV in Robin) is acquired but not yet baked into the DB or surfaced in the UI.

## Technology Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19 | UI framework |
| TypeScript | 5.9 | Type safety |
| Vite | 7 | Build tool |
| Tailwind CSS | 3.4 | Styling |
| React Router | 7 | Routing |
| Recharts | 3 | Charts |
| Axios | 1 | HTTP client |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Language |
| FastAPI | 0.104+ | API framework |
| uvicorn | 0.24+ | ASGI server |
| SQLAlchemy | 2.0+ | ORM |
| pandas | 2.1+ | Data processing |

### Hosting

| Component | Service | Detail |
|-----------|---------|--------|
| App | Docker + Caddy | Self-hosted Carson box (192.168.0.174), Cloudflare Tunnel |
| Database | SQLite (~1.3M rows, 745 MB) | Baked into Docker image; rebake via `rebake_history.py` |
| Data Pipeline | Robin collectors | Offline acquisition → Robin stores → rebake → image |

## Data Sources

| Source | Records | Coverage |
|--------|---------|----------|
| USDA NASS (history) | ~1.06M | 44 commodities, national + state, 1908–2026 |
| FAO FAOSTAT | ~167K | Producer prices by country + food CPIs |
| World Bank Pink Sheet | ~49K | CMO monthly commodity prices |
| BLS AP (retail) | ~20K | Monthly average prices 1980–2026 |
| USDA PSD | 192 MB | Supply & demand quantities (acquired, not surfaced) |

## Development Commands

### Frontend

```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server (port 3000)
npm run build        # Production build
npm run lint         # Check code quality
npm test             # Run tests (Vitest)
```

### Backend

```bash
cd backend
venv\Scripts\activate
python main.py                    # Start server (port 8000)
python -m database.import_all     # Import FRED, BLS, FAO, WB, retail data
python -m database.import_all_wasde  # Import WASDE data from Robin
pytest                            # Run tests
```

## Environment Variables

### Frontend

Set via `netlify.toml` for production, or create `.env.local`:

```
VITE_API_URL=http://localhost:8000
```

> **API base rule (critical):** `frontend/src/services/api.ts` defaults to `''` (same-origin) for production. Never reintroduce `localhost:8002` as production default — caused the 2026-06-12 regression.

### Backend

Copy `backend/.env.example` to `backend/.env`:

```
ENV=development
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
FRED_API_KEY=your_key
USDA_NASS_API_KEY=your_key
```

## Known Issues

1. **Project `backend/` lags deploy tree** — new geo/coverage endpoints and rebake script exist only under `Council/Carson/Technical/deploy/foodberg/backend/`. Reconcile when doing project-local dev.
2. **USDA PSD not surfaced** — 192 MB CSV in Robin; supply/demand data acquired but not baked into the DB and not visible in the UI (`/supply-demand` page is a placeholder).
3. **Pink Sheet URL drift** — World Bank occasionally changes the xlsx URL; re-acquire before next rebake if local store is empty.
4. **`market_prices` table empty** — USDA Market News terminal prices not imported. Live API calls require `USDA_API_KEY`.
5. **Project-local backend can lag production** — verify behavior against the Carson deploy tree before editing backend claims.
6. **Document integration incomplete** — 895 Hopper-read documents are in `Knowledge_Base/` and
   KBIP catalogs exist, but `/kb-integrate-pipeline` and `robert-db-build` remain pending.

## Critical Design Constraints

- **NO AI/forecasting/recipe/menu engineering features** — these were deliberately removed
- **NO ML predictions, WebSocket, real-time updates** — stripped for simplicity
- Historical focus: "only price charts of food" for "historically minded chefs"
- **Honest coverage badges** — no fabricated single-point trend lines; stat cards for thin series instead of misleading charts

## KB Wishlist Track

Separate from the web app, Foodberg maintains a scholarly KB acquisition wishlist:

- **Current**: `Outputs/2026.06.20 KB Wishlist v4 Global/` — 1,985 entries, 105 categories, 27-col schema v4.0
- **Historical**: v1 (370 entries, `Outputs/2026.04.12 KB Wishlist/`), v2 (825, `Outputs/2026.04.26 KB Wishlist v2/`)
- **Acquisition state (per 2026-05-19 reconciliation audit)**: 592 entries `ACQUIRED_NOT_EXTRACTED` (~802 PDFs in `Inputs/`, added 2026-05-10), 1,393 `NOT_ACQUIRED`
- **HDARP**: NOT INITIALIZED — no `Knowledge_Base/`, no `BATCH_STATE.json`. Acquired PDFs await `/preparehdarp` → `/sphdarp`.

## Documentation

- `README.md` — Project overview, architecture, and quick start
- `PROJECT_INDEX.md` — This file
- `Technical/PROGRESS_LOG.md` — current document-campaign and integration status
- `Technical/PROGRESS_LOG.md` — Development history
- `.claude/instructions.md` — Agent configuration

---

*Last updated: July 17, 2026 — living status reconciled after Hopper landing and KBIP cataloguing.*