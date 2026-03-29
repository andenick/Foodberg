# API Documentation Updates - FRED Integration

**Date**: October 23, 2025
**New Features**: FRED Economic Indicators

## Updated Database Statistics

### Database Record Counts

```json
{
  "database_stats": {
    "wasde_data": 147369,
    "economic_indicators": 1190,      // ← UPDATED
    "market_prices": 0,
    "global_prices": 0,
    "retail_prices": 0,
    "total": 148559                    // ← UPDATED
  }
}
```

## New Endpoints - Economic Indicators

### Get Economic Indicators

Fetch food-related economic indicators from FRED (Federal Reserve Economic Data).

**Endpoint**: `GET /api/economic/indicators`

**Query Parameters**:
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `series_id` | string | No | FRED series ID | `CPIUFDSL` |
| `category` | string | No | Indicator category | `CPI`, `PPI` |
| `start_date` | string | No | Start date (ISO 8601) | `2024-01-01` |
| `end_date` | string | No | End date (ISO 8601) | `2025-12-31` |
| `limit` | integer | No | Maximum results (default: 100) | `50` |

**Response**:
```json
{
  "indicators": [
    {
      "id": 1,
      "indicator_name": "Consumer Price Index - Food",
      "series_id": "CPIUFDSL",
      "value": 315.2,
      "date": "2025-09-01T00:00:00",
      "category": "CPI",
      "frequency": "Monthly",
      "source": "FRED"
    },
    {
      "id": 2,
      "indicator_name": "Producer Price Index - Farm Products",
      "series_id": "WPU01",
      "value": 108.5,
      "date": "2025-09-01T00:00:00",
      "category": "PPI",
      "frequency": "Monthly",
      "source": "FRED"
    }
  ],
  "count": 2,
  "filters": {
    "category": null,
    "series_id": null,
    "date_range": ["2024-01-01", "2025-12-31"]
  }
}
```

**Example Requests**:

```bash
# Get all indicators
curl "http://localhost:8000/api/economic/indicators"

# Get CPI indicators only
curl "http://localhost:8000/api/economic/indicators?category=CPI"

# Get specific series
curl "http://localhost:8000/api/economic/indicators?series_id=CPIUFDSL"

# Get indicators for date range
curl "http://localhost:8000/api/economic/indicators?start_date=2024-01-01&end_date=2024-12-31"
```

---

### Get Indicator Trends

Get time series trend for a specific economic indicator.

**Endpoint**: `GET /api/economic/trends/{series_id}`

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `series_id` | string | **Yes** | FRED series ID |

**Query Parameters**:
| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `period` | string | No | Time period | `1year`, `5years`, `all` | `1year` |

**Response**:
```json
{
  "series_id": "CPIUFDSL",
  "indicator_name": "Consumer Price Index - Food",
  "category": "CPI",
  "period": "1year",
  "data": [
    {
      "date": "2024-10-01",
      "value": 312.5
    },
    {
      "date": "2024-11-01",
      "value": 313.1
    },
    {
      "date": "2024-12-01",
      "value": 314.2
    }
    // ... more data points
  ],
  "statistics": {
    "count": 12,
    "min": 312.5,
    "max": 315.2,
    "avg": 313.8,
    "change": 2.7,
    "percent_change": 0.86
  }
}
```

**Example Requests**:
```bash
# Get 1 year trend for Food CPI
curl "http://localhost:8000/api/economic/trends/CPIUFDSL"

# Get 5 year trend for Farm Products PPI
curl "http://localhost:8000/api/economic/trends/WPU01?period=5years"

# Get all historical data
curl "http://localhost:8000/api/economic/trends/CPIUFDSL?period=all"
```

---

### Compare Indicators

Compare multiple economic indicators over time.

**Endpoint**: `GET /api/economic/compare`

**Query Parameters**:
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `series_ids` | string | **Yes** | Comma-separated series IDs | `CPIUFDSL,WPU01` |
| `start_date` | string | No | Start date | `2024-01-01` |
| `end_date` | string | No | End date | `2025-12-31` |

**Response**:
```json
{
  "comparison": {
    "series": [
      {
        "series_id": "CPIUFDSL",
        "name": "Consumer Price Index - Food",
        "category": "CPI",
        "data": [
          {"date": "2024-01-01", "value": 310.5},
          {"date": "2024-02-01", "value": 311.2}
        ],
        "statistics": {
          "min": 310.5,
          "max": 315.2,
          "avg": 312.8,
          "change": 4.7,
          "percent_change": 1.51
        }
      },
      {
        "series_id": "WPU01",
        "name": "Producer Price Index - Farm Products",
        "category": "PPI",
        "data": [
          {"date": "2024-01-01", "value": 105.2},
          {"date": "2024-02-01", "value": 106.1}
        ],
        "statistics": {
          "min": 105.2,
          "max": 108.5,
          "avg": 106.9,
          "change": 3.3,
          "percent_change": 3.14
        }
      }
    ],
    "date_range": ["2024-01-01", "2025-12-31"],
    "correlation": 0.78
  }
}
```

**Example Request**:
```bash
curl "http://localhost:8000/api/economic/compare?series_ids=CPIUFDSL,WPU01&start_date=2024-01-01"
```

---

## Available FRED Series

The following economic indicator series are available:

### Consumer Price Index (CPI)

| Series ID | Name | Description |
|-----------|------|-------------|
| `CPIUFDSL` | Consumer Price Index - Food | Overall food price index |
| `CPIUFDNS` | CPI - Food and Beverages | Food and beverage price index |
| `CUSR0000SAF11` | CPI - Food at Home | Prices for food consumed at home |
| `CUSR0000SEFV` | CPI - Food Away from Home | Restaurant and prepared food prices |
| `CPIAUCSL` | CPI - All Items | Overall consumer price index |

### Producer Price Index (PPI)

| Series ID | Name | Description |
|-----------|------|-------------|
| `WPU01` | PPI - Farm Products | Prices farmers receive for products |
| `PPIFID` | PPI - Finished Goods: Food | Finished food product prices |
| `WPU0211` | PPI - Grains | Grain commodity prices |
| `WPU0212` | PPI - Livestock and Poultry | Livestock and poultry prices |
| `PPIACO` | PPI - All Commodities | Overall commodity price index |

**Total Series**: 10
**Total Observations**: 1,190 (10 years, monthly data)
**Last Updated**: October 23, 2025

---

## Updated Data Models

### EconomicIndicator

```typescript
interface EconomicIndicator {
  id: number
  indicator_name: string          // e.g., "Consumer Price Index - Food"
  series_id: string                // FRED series ID (e.g., "CPIUFDSL")
  value: number                    // Indicator value
  date: string                     // Observation date (ISO 8601)
  category: string                 // "CPI" or "PPI"
  frequency: string                // "Monthly", "Quarterly", or "Annual"
  source: string                   // Always "FRED"
  imported_at: string              // Import timestamp
}
```

---

## Usage Examples

### Python Example

```python
import requests

# Get all CPI indicators
response = requests.get(
    'http://localhost:8000/api/economic/indicators',
    params={'category': 'CPI'}
)
cpi_data = response.json()

print(f"Found {cpi_data['count']} CPI indicators")

# Get Food CPI trend
response = requests.get(
    'http://localhost:8000/api/economic/trends/CPIUFDSL',
    params={'period': '1year'}
)
trend = response.json()

print(f"Food CPI change: {trend['statistics']['percent_change']}%")

# Compare CPI and PPI
response = requests.get(
    'http://localhost:8000/api/economic/compare',
    params={
        'series_ids': 'CPIUFDSL,WPU01',
        'start_date': '2024-01-01'
    }
)
comparison = response.json()

print(f"CPI vs PPI correlation: {comparison['correlation']}")
```

### JavaScript Example

```javascript
// Get all economic indicators
const indicators = await fetch('http://localhost:8000/api/economic/indicators')
  .then(res => res.json());

console.log(`Total indicators: ${indicators.count}`);

// Get specific series trend
const trend = await fetch(
  'http://localhost:8000/api/economic/trends/CPIUFDSL?period=1year'
).then(res => res.json());

console.log(`Food CPI trend:`, trend.statistics);

// Compare multiple indicators
const comparison = await fetch(
  'http://localhost:8000/api/economic/compare?series_ids=CPIUFDSL,WPU01,PPIFID'
).then(res => res.json());

console.log(`Series comparison:`, comparison);
```

---

## Integration Notes

### Combining WASDE and FRED Data

You can correlate commodity prices (WASDE) with economic indicators (FRED) to analyze price movements in economic context:

```python
import requests
from datetime import datetime

# Get wheat prices
wheat_prices = requests.get(
    'http://localhost:8000/api/prices/search',
    params={'commodity': 'WHEAT', 'limit': 100}
).json()

# Get Food CPI for same period
food_cpi = requests.get(
    'http://localhost:8000/api/economic/trends/CPIUFDSL',
    params={'period': '1year'}
).json()

# Analyze correlation
# ... your analysis code
```

### Real-Time Updates

FRED data can be updated using the FRED client:

```bash
cd backend
python -m database.importers.fred_client
```

This will fetch the latest 10 years of monthly data for all configured series.

---

## Changelog

### October 23, 2025 - v1.1

**Added:**
- FRED economic indicators support (1,190 observations)
- 3 new API endpoints for economic data
- 10 food-related indicator series (5 CPI + 5 PPI)
- Time series trend analysis
- Multi-series comparison functionality

**Updated:**
- Database statistics now include economic_indicators table
- Total records: 147,369 → 148,559
- Data sources: 1 (WASDE) → 2 (WASDE + FRED)

---

**Integration Status**: ✅ Complete
**Data Source**: Federal Reserve Economic Data (FRED)
**API Key**: Loaded from Robin's api_keys.json
**Update Frequency**: Monthly (manual import)
