# Foodberg Inputs/ Directory

**Purpose**: Read-only storage for original input files per Arcanum workspace standards.

## Structure

FLAT — no type-based subdirectories. All 71 commodity JSON files sit directly in this directory.

```
Inputs/
├── README.md
├── [2025.09.25] wheat_2025-09-25.json
├── [2025.09.25] corn_2025-09-25.json
├── ... (71 commodity price snapshot files)
└── [2025.09.25] collection_summary_2025-09-25.json
```

## Contents

71 commodity price JSON files collected September 25, 2025. Each contains:
- Current retail price, unit, category
- Source (USDA)
- Raw API data with lastUpdated timestamp

Categories: grains, proteins, dairy, produce, fruits, nuts, spices, oils, beverages

## Usage Rules

1. **Read-Only**: Files in Inputs/ should NEVER be modified
2. **Originals Only**: Store only original, unprocessed files
3. **Processing**: Import into database via `python -m database.import_all`
4. **No Generated Files**: Do not store derived/processed data here

## Data Sources

Primary data sources are accessed from Robin's canonical locations:

- **WASDE Data**: `Inputs/robin/DATA/USDA_WASDE/ (set ROBIN_DATA_DIR env var)` (35 commodity files)
- **Historical Prices**: `Inputs/robin/DATA/OTHER_APIS/USDA_FOOD/data/historical/` (85 files)
- **FRED**: `Inputs/robin/DATA/FRED/fred_data/fred_data.db`
- **BLS CPI**: `Inputs/robin/API_MODULES/BLS/data/`
- **FAO**: `Inputs/robin/DATA/FAO/`
- **World Bank**: `Inputs/robin/DATA/WorldBank/WDI_CSV/`
- **API Keys**: `backend/config/` (see api_keys.json.template)

**Compliance Status**: 100% (FLAT structure, Druck compliant)
**Last Updated**: 2026-04-04
