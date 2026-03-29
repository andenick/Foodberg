# Foodberg - Historical Food Price Explorer

A simple data visualization app for exploring historical food commodity prices, built with React and FastAPI.

## What It Does

- **Food Price Index**: Composite indices for 6 food groups (meat, dairy, cereals, oils, sugar, produce) from FAO and BLS data, covering 1990-present
- **Price Explorer**: Browse 50+ agricultural commodities from USDA WASDE data
- **Geographic Comparison**: Compare prices across US states and regions
- **Historical Trends**: Multi-commodity comparison with correlation analysis
- **Data Sources**: USDA WASDE, FRED, BLS CPI, FAO Food Price Index, World Bank

## Data

166,000+ price records from 5 sources:

| Source | Records | Coverage |
|--------|---------|----------|
| USDA WASDE | 147,369 | 50 US agricultural commodities (grains, livestock, dairy, fruits) |
| FRED | 10,290 | CPI, PPI, interest rates, economic indicators |
| BLS CPI | 840 | Food at Home, Food Away, 5 sub-components (2015-2025) |
| FAO | 2,586 | Global food price indices: meat, dairy, cereals, oils, sugar (1990-2025) |
| World Bank | 2,705 | Agricultural production/trade indicators for 9 countries |

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m database.import_all    # Populate database (first time only)
python main.py                   # Starts on http://localhost:8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev                      # Starts on http://localhost:3000
```

## Tech Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Recharts
- **Backend**: FastAPI, Python, SQLite, SQLAlchemy
- **Data**: Robin (WASDE, FRED, BLS, FAO, World Bank)

## Hosting Plan

| Component | Service | Cost |
|-----------|---------|------|
| Frontend | Netlify | Free |
| Backend | Render | Free |
| Database | SQLite + Litestream | Free |

## Project Structure

```
Foodberg/
  backend/           # FastAPI server
    main.py          # API endpoints
    database/        # SQLAlchemy models, importers
    indices/         # Composite index computation
    data/            # SQLite database
    data_sources/    # API clients (FRED, FAO, World Bank, USDA)
  frontend/          # React app
    src/pages/       # 7 pages (Home, Index, Explorer, Detail, Geographic, Trends, Sources)
    src/services/    # API client
  Inputs/            # Raw data (70 commodity JSON files)
  Technical/         # Processing scripts
  Outputs/           # Deliverables
```
