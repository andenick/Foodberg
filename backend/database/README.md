# Foodberg Price Database

Comprehensive SQLite database for agricultural commodity prices and statistics, integrating multiple data sources including USDA WASDE, Market News, FRED economic indicators, FAO global prices, and World Bank data.

## Overview

**Database**: SQLite 3
**Records**: 147,369 WASDE records (as of October 2025)
**Commodities**: 35+ agricultural commodities
**Time Span**: Historical data from multiple years
**Size**: 66 MB

## Database Schema

### Tables

#### 1. `wasde_data` - USDA WASDE Agricultural Statistics
Primary data source for US agricultural commodity statistics.

**Columns:**
- `id` (INTEGER, PRIMARY KEY) - Auto-incrementing record ID
- `commodity` (VARCHAR(100), INDEXED) - Commodity name (e.g., "WHEAT", "CORN", "SOYBEANS")
- `statistic_category` (VARCHAR(200), INDEXED) - Category (e.g., "PRICE RECEIVED", "PRODUCTION")
- `value` (VARCHAR(100)) - Original value as string
- `numeric_value` (FLOAT) - Parsed numeric value
- `unit` (VARCHAR(50)) - Unit of measurement (e.g., "$ / BU", "TONS")
- `location` (VARCHAR(100), INDEXED) - Geographic location (state or "US TOTAL")
- `state_code` (VARCHAR(2)) - Two-letter state code
- `year` (INTEGER, INDEXED) - Year of observation
- `month` (INTEGER) - Month (if available)
- `period` (VARCHAR(50)) - Time period description
- `short_desc` (TEXT) - Full description
- `domain_desc` (VARCHAR(100)) - Data domain
- `commodity_code` (VARCHAR(20)) - USDA commodity code
- `asd_desc` (VARCHAR(100)) - Agricultural Statistics District
- `county_name` (VARCHAR(100)) - County (if applicable)
- `zip_code` (VARCHAR(10)) - ZIP code (if applicable)
- `region_desc` (VARCHAR(100)) - Region description
- `watershed_code` (VARCHAR(20)) - Watershed code (if applicable)
- `reference_period_desc` (VARCHAR(100)) - Reference period
- `source` (VARCHAR(50), DEFAULT 'WASDE') - Data source
- `imported_at` (TIMESTAMP) - Import timestamp

**Indexes:**
- `ix_wasde_commodity` - Single column index on commodity
- `ix_wasde_statistic_category` - Single column index on statistic_category
- `ix_wasde_location` - Single column index on location
- `ix_wasde_year` - Single column index on year
- `ix_wasde_commodity_year` - Composite index on (commodity, year)
- `ix_wasde_commodity_location` - Composite index on (commodity, location)

**Record Count**: 147,369

#### 2. `market_prices` - USDA Market News Terminal Prices
Real-time and historical wholesale market prices.

**Columns:**
- `id` (INTEGER, PRIMARY KEY)
- `commodity` (VARCHAR(100), INDEXED)
- `market` (VARCHAR(100)) - Terminal market name
- `price` (FLOAT) - Price value
- `unit` (VARCHAR(50)) - Price unit
- `date` (DATE, INDEXED) - Price date
- `grade` (VARCHAR(50)) - Product grade
- `source` (VARCHAR(50))
- `imported_at` (TIMESTAMP)

**Indexes:**
- `ix_market_commodity_date` - Composite index on (commodity, date)

**Record Count**: 0 (framework ready, pending data sync)

#### 3. `economic_indicators` - FRED Economic Data
Economic indicators affecting agricultural markets.

**Columns:**
- `id` (INTEGER, PRIMARY KEY)
- `indicator_name` (VARCHAR(100), INDEXED)
- `value` (FLOAT)
- `date` (DATE, INDEXED)
- `unit` (VARCHAR(50))
- `frequency` (VARCHAR(20))
- `source` (VARCHAR(50))
- `imported_at` (TIMESTAMP)

**Indexes:**
- `ix_indicator_name_date` - Composite index on (indicator_name, date)

**Record Count**: 0 (framework ready, pending data sync)

#### 4. `global_prices` - FAO Global Food Prices
International food price data from FAO.

**Columns:**
- `id` (INTEGER, PRIMARY KEY)
- `commodity` (VARCHAR(100), INDEXED)
- `country` (VARCHAR(100))
- `price` (FLOAT)
- `unit` (VARCHAR(50))
- `date` (DATE, INDEXED)
- `source` (VARCHAR(50))
- `imported_at` (TIMESTAMP)

**Record Count**: 0 (framework ready, pending data sync)

#### 5. `retail_prices` - Retail Food Prices
Consumer-level retail prices.

**Columns:**
- `id` (INTEGER, PRIMARY KEY)
- `commodity` (VARCHAR(100), INDEXED)
- `location` (VARCHAR(100))
- `price` (FLOAT)
- `unit` (VARCHAR(50))
- `date` (DATE, INDEXED)
- `store_type` (VARCHAR(50))
- `source` (VARCHAR(50))
- `imported_at` (TIMESTAMP)

**Record Count**: 0 (framework ready, pending data sync)

#### 6. `data_source_sync` - Data Synchronization Tracking
Tracks data import and sync operations.

**Columns:**
- `id` (INTEGER, PRIMARY KEY)
- `source_name` (VARCHAR(100), INDEXED) - Data source identifier
- `last_sync` (TIMESTAMP) - Last successful sync timestamp
- `status` (VARCHAR(20)) - "SUCCESS", "FAILED", "PENDING"
- `records_imported` (INTEGER) - Number of records imported
- `error_message` (TEXT) - Error details if failed

## Data Sources

### 1. USDA WASDE (World Agricultural Supply and Demand Estimates)
**Status**: ✅ Active (147,369 records imported)
**Update Frequency**: Monthly
**Coverage**: US agricultural commodities
**Data Location**: `D:/Arcanum/Council/Robin/Data/USDA_NASS/WASDE_JSON/`

### 2. USDA Market News
**Status**: ⏳ Framework ready, pending sync
**Update Frequency**: Daily
**Coverage**: Terminal market prices

### 3. FRED (Federal Reserve Economic Data)
**Status**: ⏳ Framework ready, pending sync
**Update Frequency**: Variable (daily to monthly)
**Coverage**: Economic indicators (CPI, PPI, inflation)

### 4. FAO (Food and Agriculture Organization)
**Status**: ⏳ Framework ready, pending sync
**Update Frequency**: Monthly
**Coverage**: Global food prices

### 5. World Bank Commodity Prices
**Status**: ⏳ Framework ready, pending sync
**Update Frequency**: Monthly
**Coverage**: International commodity prices

### 6. API Ninja Food Prices
**Status**: ⏳ Framework ready, pending sync
**Update Frequency**: Daily
**Coverage**: Retail and wholesale prices

## Usage

### Python API

```python
from database.manager import DatabaseManager

# Initialize database connection
db = DatabaseManager()

# Search for wheat prices
results = db.search_prices(
    commodity="WHEAT",
    sources=["wasde"],
    start_date=None,
    end_date=None,
    location="US TOTAL",
    limit=100
)

# Get price statistics
stats = db.get_wasde_statistics("WHEAT")
print(f"Average wheat price: ${stats['avg_price']:.2f}")
print(f"Price range: ${stats['min_price']:.2f} - ${stats['max_price']:.2f}")

# Get trend data
trends = db.get_wasde_trend("WHEAT", period_years=1)
```

### REST API Endpoints

See [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) for complete API reference.

**Base URL**: `http://localhost:8000`

#### Search Prices
```bash
GET /api/prices/search?commodity=WHEAT&sources=wasde&limit=100
```

#### Get Statistics
```bash
GET /api/prices/stats/WHEAT
```

#### Get Price Trends
```bash
GET /api/prices/trend/WHEAT?period=1year
```

#### Compare Prices
```bash
GET /api/prices/compare/WHEAT?year=2025
```

#### Database Statistics
```bash
GET /api/prices/database/stats
```

## Data Import

### Initial Migration

```bash
cd backend
python database/migrate.py
```

**Output**:
```
[INFO] Creating database tables...
[OK] Database schema created
[INFO] Starting WASDE data import...
[OK] Imported 147,369 records in 26.1 seconds
[OK] Migration complete
```

### Performance Metrics
- **Import Speed**: 5,650 records/second
- **Database Size**: 66 MB
- **Query Performance**: < 100ms for most queries
- **Batch Size**: 1,000 records per transaction

## Data Quality

### Value Normalization

The importer handles various value formats:
- **Numeric**: `"5.52"` → `5.52`
- **Comma-separated**: `"209,442,000"` → `209442000.0`
- **Ranges**: `"5.50-6.00"` → `5.75` (midpoint)
- **Withheld**: `"(D)"` → `None`
- **Suppressed**: `"(S)"` → `None`

### Data Integrity
- ✅ All 147,369 WASDE records imported successfully
- ✅ Zero import errors
- ✅ 2,376 price records with numeric values
- ✅ 35 commodities represented
- ✅ Composite indexes for optimized queries

## Maintenance

### Update WASDE Data
```python
from database.importers.wasde_importer import WASDEDataImporter

importer = WASDEDataImporter(db_manager)
importer.import_from_directory()
```

### Sync Live Data Sources
```python
from database.importers.live_sync import LiveDataSync

sync = LiveDataSync(db_manager)
await sync.sync_usda_market_news()
await sync.sync_fred_indicators()
await sync.sync_fao_prices()
```

### Check Sync Status
```python
status = db.get_sync_status()
for source in status:
    print(f"{source['source']}: {source['status']} - {source['records']} records")
```

## Troubleshooting

### Issue: Import errors with Unicode characters
**Solution**: Encoding automatically handled by importer. Uses UTF-8 with fallback to ASCII.

### Issue: Slow query performance
**Solution**: Database includes composite indexes. Run `ANALYZE` periodically:
```python
db.engine.execute("ANALYZE")
```

### Issue: Large database file size
**Solution**: Use SQLite VACUUM to reclaim space:
```python
db.engine.execute("VACUUM")
```

## Development

### Adding New Data Sources

1. Create importer in `database/importers/`
2. Define sync method in `LiveDataSync` class
3. Add table model in `database/models.py`
4. Update `DatabaseManager` with query methods
5. Create API endpoint in `main.py`

### Testing

```bash
cd backend
python test_database.py
```

## File Locations

- **Database**: `backend/data/foodberg.db`
- **Models**: `backend/database/models.py`
- **Manager**: `backend/database/manager.py`
- **Importers**: `backend/database/importers/`
- **Migration**: `backend/database/migrate.py`
- **Tests**: `backend/test_database.py`

## Credits

**Data Sources**:
- USDA National Agricultural Statistics Service (NASS)
- USDA Agricultural Marketing Service (Market News)
- Federal Reserve Economic Data (FRED)
- Food and Agriculture Organization (FAO)
- World Bank
- API Ninja

**Robin Council Tool**: Data collection and curation
**Foodberg Backend**: Database integration and API
**Built with**: SQLAlchemy 2.0.31, SQLite 3, FastAPI

## License

Data is sourced from public government and international organization databases. See individual data source terms of use.
