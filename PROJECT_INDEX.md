# Foodberg - Complete Project Index

## Purpose

Historical Food Price Explorer — a data visualization app for understanding food commodity prices and their history. Built for historically minded chefs who want to understand the broader environmental and historical context of food prices.

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

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (dev mode only)

## Project Structure

```
Foodberg/
  backend/              # FastAPI server (Python)
    main.py             # API endpoints (24 GET routes)
    database/           # SQLAlchemy models, importers, manager
    indices/            # Composite index computation
    data/               # SQLite database (foodberg.db)
    data_sources/       # API clients (FRED, FAO, World Bank, USDA, Robin)
    config/             # API key configuration
  frontend/             # React app (TypeScript)
    src/pages/          # 7 pages
    src/services/       # API client (api.ts)
    src/components/     # Header, Footer
  Inputs/               # Raw data (70 commodity JSON files)
  Technical/            # Processing scripts, docs, progress log
  Outputs/              # Deliverables (placeholder structure)
```

## Frontend Pages

| Route | Page | Data Source |
|-------|------|-------------|
| `/` | HomePage | Static content |
| `/index` | FoodPriceIndex | `GET /api/indices/`, `GET /api/indices/{category}` |
| `/explore` | PriceExplorer | `GET /api/wasde/commodities`, `GET /api/wasde/{commodity}` |
| `/commodity/:id` | CommodityDetail | `GET /api/wasde/{id}` |
| `/geographic` | GeographicPrices | `GET /api/wasde/{commodity}` |
| `/trends` | HistoricalTrends | `GET /api/wasde/{commodity}` (parallel) |
| `/sources` | DataSources | `GET /api/data/sources`, `GET /api/data/status` |

## API Endpoints (24 GET routes)

### Core
- `GET /` — API root (name, version, status)
- `GET /api/health` — Health check
- `GET /api/data/status` — Per-table record counts, date ranges, freshness
- `GET /api/data/sources` — Static source metadata

### WASDE Commodities (from database)
- `GET /api/wasde/commodities` — List available commodities from Robin data store
- `GET /api/wasde/{commodity}` — All records for a commodity (params: `limit`)
- `GET /api/wasde/{commodity}/national` — National-level data
- `GET /api/wasde/{commodity}/state/{state}` — State-level data

### Price Search
- `GET /api/prices/search` — Unified search across sources
- `GET /api/prices/trend/{commodity}` — Price trend with period filter
- `GET /api/prices/compare/{commodity}` — Cross-source comparison
- `GET /api/prices/stats/{commodity}` — Price statistics
- `GET /api/prices/database/stats` — Database record counts
- `GET /api/prices/terminal/{market}` — Live USDA Market News (requires API key)

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

SQLite database at `backend/data/foodberg.db` with 6 tables:

| Table | Records | Source |
|-------|---------|--------|
| `wasde_data` | 147,369 | Robin/USDA NASS (50 commodities) |
| `economic_indicators` | 13,185 | FRED (21 series) + BLS CPI (7 series) |
| `global_prices` | 5,722 | FAO Food Price Index + World Bank WDI |
| `retail_prices` | 70 | Inputs/ commodity JSON files |
| `composite_indices` | 2,715 | Computed from FAO + BLS data |
| `market_prices` | 0 | USDA Market News (not populated) |
| **Total** | **169,061** | |

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

### Hosting Plan

| Component | Service | Cost |
|-----------|---------|------|
| Frontend | Netlify | Free |
| Backend | Render | Free |
| Database | SQLite + Litestream | Free |

## Data Sources

| Source | Records | Coverage |
|--------|---------|----------|
| USDA WASDE (via Robin) | 147,369 | 50 US agricultural commodities |
| FRED | 10,290 | 21 economic indicator series |
| BLS CPI | 840 | 7 food CPI sub-components (2015-2025) |
| FAO | 2,586 | Global food price indices (1990-2025) |
| World Bank | 2,705 | Agricultural indicators for 9 countries |
| Inputs/ retail | 70 | Commodity snapshots |

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

### Backend

Copy `backend/.env.example` to `backend/.env`:

```
ENV=development
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
FRED_API_KEY=your_key
USDA_API_KEY=your_key  # For live terminal market prices only
```

## Known Issues

1. **`market_prices` table empty** — USDA Market News terminal prices not imported. The `/api/prices/terminal/{market}` endpoint makes live API calls requiring a `USDA_API_KEY`.
2. **Render cold starts** — Free tier sleeps after 15 min, ~30s wake-up delay.
3. **Not deployed yet** — Working locally; deployment deferred.

## Critical Design Constraints

- **NO AI/forecasting/recipe/menu engineering features** — these were deliberately removed
- **NO ML predictions, WebSocket, real-time updates** — stripped for simplicity
- Historical focus: "only price charts of food" for "historically minded chefs"

## Documentation

- `README.md` — Project overview and quick start
- `HANDOFF_DOCUMENTATION.md` → `Technical/Handoffs/HANDOFF_20260328_000000.md`
- `Technical/[2025.10.08] PROGRESS_LOG.md` — Development history
- `.claude/instructions.md` — Agent configuration

---

*Last updated: April 3, 2026*
