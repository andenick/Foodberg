# Foodberg — Historical Food Price Explorer

**🟢 LIVE AT [foodberg.org](https://foodberg.org)** — A full-stack web application for exploring historical food commodity prices, built with React and FastAPI. Its multi-source SQLite build covers USDA NASS history, USDA PSD, World Bank Pink Sheet, FAO producer prices, and BLS retail data, with honest coverage badges rather than fabricated trend lines.

> **Project state:** Deployed via Carson on a self-hosted Docker box behind Cloudflare Tunnel (FastAPI + Caddy → SPA). Data is acquired by the maintainer's collectors, rebaked through `rebake_history.py`, and baked into the production Docker image. Multi-source Price Explorer with source-picker tabs; three-mode Geographic page (FAOSTAT producer, US state NASS, World Bank indicators); honest coverage badges — no fabricated trend lines.

> **Living status (verified 2026-07-17):** the website remains active and live. The separate
> document track has advanced: **895 Hopper-read documents** were landed in `Knowledge_Base/`,
> method-tagged, catalogued, and packaged to offline archive storage on 2026-07-16. The canonical
> `/kb-integrate-pipeline` pass and the downstream RobertDB build are still pending; do not
> describe Foodberg as having a completed RobertDB. Current evidence is in
> the maintainer's private processing log.

---

## Why This Exists

Understanding food prices requires combining data from scattered government sources (USDA, BLS, FAO, World Bank) into a single queryable interface. Foodberg harmonizes these into a SQLite database with a React frontend for interactive exploration — designed for researchers, journalists, and historically minded chefs who want to see the data behind the food system.

---

## Architecture

```
data sources  ──►  rebake_history.py  ──►  foodberg.db  ──►  Docker image
                                                          │
foodberg/frontend           ──npm build──►  dist/  ──────┤
                                                          ▼
                                              foodberg.org (Caddy → FastAPI + SPA)
```

Data is acquired offline by the maintainer's collectors into a private data store (NASS history, FAOSTAT bulk, Pink Sheet, BLS AP). The rebake script (`backend/database/rebake_history.py` in the deploy tree) reads from those stores and produces `foodberg.db`, which is baked into the Docker image. No runtime API calls in production.

---

## Quick Start

```bash
git clone https://github.com/<your-username>/Foodberg.git
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

- **Price Explorer**: Multi-source price browsing with source-picker tabs (NASS farm gate, global spot/Pink Sheet, BLS retail). Coverage badges and stat cards for thin series. CSV download per chart.
- **Geographic Comparison**: Three-mode toggle — FAOSTAT producer prices by country, US state NASS prices, World Bank development indicators.
- **Historical Trends**: Multi-commodity line charts; eligibility restricted to commodities with real multi-year history.
- **Food Price Index**: Composite indices for 6 food groups (meat, dairy, cereals, oils, sugar, produce) from FAO and BLS data.
- **Data Sources**: Database overview with per-source record counts and status cards.

---

## Data Sources

| Source | Records | Coverage | Access |
|--------|---------|----------|--------|
| USDA NASS (history) | ~1.06M | 44 commodities, national + state prices, 1908–2026 | [USDA Quick Stats](https://quickstats.nass.usda.gov/) |
| FAO FAOSTAT | ~167K | Producer prices by country + country food CPIs | [FAOSTAT Bulk](https://www.fao.org/faostat/en/#data/) |
| World Bank Pink Sheet | ~49K | CMO monthly commodity prices | [World Bank CMO](https://www.worldbank.org/en/research/commodity-markets) |
| BLS AP (retail) | ~20K | Average price series, monthly 1980–2026 | [BLS](https://www.bls.gov/cpi/) via FRED mirror |
| World Bank WDI | ~3K | Development indicators | [WDI](https://data.worldbank.org/) |
| USDA PSD | 192 MB | Supply & demand quantities (acquired, not surfaced in UI) | [USDA PSD](https://apps.fas.usda.gov/psdonline/) |
| Composite Indices | ~3K | Computed from FAO + BLS data | Derived |

---

## Repository Structure

```
Foodberg/
├── README.md
├── backend/                FastAPI server (project-local, lags deploy tree)
│   ├── main.py             API endpoints
│   ├── database/           SQLAlchemy models, importers
│   ├── indices/            Composite index computation
│   ├── data/               SQLite database (foodberg.db)
│   └── data_sources/       API clients (FRED, FAO, World Bank, USDA)
├── frontend/               React app (canonical source for frontend)
│   └── src/pages/          9 pages (Home, PriceIndex, Explorer, Detail, Geographic, Trends, Sources, Downloads, SupplyDemand)
├── Inputs/                 Raw data & ~802 acquired PDFs (gitignored)
├── Technical/              Processing scripts, docs, progress log
└── Outputs/                Deliverables (wishlists, PSD exports)
```

> **Deploy tree (canonical production backend):** the maintainer's private deploy tree — includes main.py, worldbank_client.py, rebake_history.py, and the baked `data/foodberg.db` (gitignored, in Docker image only).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, Recharts |
| Backend | FastAPI, Python, SQLAlchemy |
| Database | SQLite, multi-million-row production build (exact counts vary by rebake) |
| Deployment | Docker + Caddy + Cloudflare Tunnel (self-hosted Carson box) |
| Data Pipeline | offline collectors → rebake_history.py → baked image |

---

## Requirements

- **Python 3.11+** — backend
- **Node.js 18+** — frontend
- **API keys** (optional) — `USDA_NASS_API_KEY` for the NASS collector, `FRED_API_KEY` for FRED data refresh

---

## Citation

```bibtex
@software{foodberg2026,
  title = {Foodberg: Historical Food Price Explorer},
  author = {Anderson, Nicholas},
  year = {2026},
  url = {https://foodberg.org}
}
```

---

## License

MIT