# Foodberg — Historical Food Price Explorer

**A full-stack web application for exploring historical food commodity prices, built with React and FastAPI. ~166,500 records from 5 public data sources (plus derived composite indices) covering 50+ agricultural commodities.**

> **Project state:** A historical food-price explorer that harmonizes public commodity data into a single SQLite database (~166,500 records) behind a React frontend and a FastAPI backend. It runs locally; it is not a deployed/hosted service. See the data-source table below for per-source record counts and provenance.

---

## Why This Exists

Understanding food prices requires combining data from scattered government sources (USDA, BLS, FAO, World Bank, FRED) into a single queryable interface. Foodberg harmonizes these into a SQLite database with a React frontend for interactive exploration — designed for researchers, journalists, and historically minded chefs who want to see the data behind the food system.

---

## Quick Start

```bash
git clone https://github.com/andenick/Foodberg.git
cd Foodberg

# Backend
cd backend
python -m venv venv
venv\Scripts\activate            # Windows (or: source venv/bin/activate)
pip install -r requirements.txt
python -m database.import_all    # Populate database from public APIs
python main.py                   # Starts on http://localhost:8000

# Frontend (new terminal)
cd ../frontend
npm install
npm run dev                      # Starts on http://localhost:3000
```

---

## Features

- **Food Price Index**: Composite indices for 6 food groups (meat, dairy, cereals, oils, sugar, produce) from FAO and BLS data, 1990–present
- **Price Explorer**: Browse 50+ agricultural commodities from USDA WASDE data
- **Geographic Comparison**: Compare prices across US states and regions
- **Historical Trends**: Multi-commodity comparison with correlation analysis
- **Live Terminal Prices**: USDA Market News API integration (requires `USDA_API_KEY`)

---

## Data Sources

| Source | Records | Coverage | Access |
|--------|---------|----------|--------|
| USDA WASDE | 147,369 | 50 US agricultural commodities (grains, livestock, dairy, fruits) | [USDA ERS](https://www.ers.usda.gov/data-products/wheat-data/) |
| FRED | 10,290 | CPI, PPI, interest rates, economic indicators | [FRED API](https://fred.stlouisfed.org/docs/api/) |
| BLS CPI | 840 | Food at Home, Food Away, 5 sub-components (2015–2025) | [BLS](https://www.bls.gov/cpi/) |
| FAO | 2,586 | Global food price indices: meat, dairy, cereals, oils, sugar (1990–2025) | [FAO FPMA](https://www.fao.org/worldfoodsituation/foodpricesindex/) |
| World Bank | 2,705 | Agricultural production/trade indicators for 9 countries | [WDI](https://data.worldbank.org/) |
| Composite Indices | 2,715 | Computed from FAO + BLS data | Derived |

---

## Repository Structure

```
Foodberg/
├── README.md
├── backend/                FastAPI server (24 GET endpoints)
│   ├── main.py             API endpoints
│   ├── database/           SQLAlchemy models, importers
│   ├── indices/            Composite index computation
│   ├── data/               SQLite database (foodberg.db)
│   └── data_sources/       API clients (FRED, FAO, World Bank, USDA)
├── frontend/               React app
│   └── src/pages/          7 pages (Home, Index, Explorer, Detail, Geographic, Trends, Sources)
├── Inputs/                 Raw data (gitignored — re-downloadable from public APIs)
├── Technical/              Processing scripts, docs, deployment configs
└── Outputs/                Deliverables
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, Recharts |
| Backend | FastAPI, Python, SQLAlchemy |
| Database | SQLite (~166.5K records) |
| Deployment | Netlify (frontend) + Render (backend), all free tier |

---

## Requirements

- **Python 3.11+** — backend
- **Node.js 18+** — frontend
- **API keys** (optional) — `USDA_API_KEY` for live terminal prices, `FRED_API_KEY` for FRED data refresh

---

## Citation

```bibtex
@software{foodberg2026,
  title = {Foodberg: Historical Food Price Explorer},
  author = {Anderson, Nicholas},
  year = {2026},
  url = {https://github.com/andenick/Foodberg}
}
```

---

## License

MIT
