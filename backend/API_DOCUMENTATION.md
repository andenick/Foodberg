# Foodberg Price Database API Documentation

Complete REST API reference for the Foodberg Food Price Database.

**Base URL**: `http://localhost:8000`
**API Version**: 1.0
**Last Updated**: October 23, 2025

## Table of Contents

- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Search Prices](#search-prices)
  - [Price Trends](#price-trends)
  - [Price Comparison](#price-comparison)
  - [Price Statistics](#price-statistics)
  - [Database Statistics](#database-statistics)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limits](#rate-limits)
- [Examples](#examples)

## Authentication

Currently, the API does not require authentication for read operations. This may change in future versions.

## Endpoints

### Search Prices

Search for commodity prices across multiple data sources with optional filters.

**Endpoint**: `GET /api/prices/search`

**Parameters**:
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `commodity` | string | **Yes** | Commodity name (uppercase) | `WHEAT` |
| `sources` | string | No | Comma-separated data sources | `wasde,usda_market_news` |
| `start_date` | string | No | Start date (ISO 8601) | `2024-01-01` |
| `end_date` | string | No | End date (ISO 8601) | `2025-12-31` |
| `location` | string | No | Geographic location filter | `US TOTAL` |
| `limit` | integer | No | Maximum results (default: 100) | `50` |

**Response**:
```json
{
  "commodity": "WHEAT",
  "sources": ["wasde"],
  "filters": {
    "start_date": "2024-01-01",
    "end_date": "2025-12-31",
    "location": "US TOTAL"
  },
  "results": {
    "wasde": [
      {
        "id": 101709,
        "commodity": "WHEAT",
        "statistic_category": "PRICE RECEIVED",
        "value": "5.52",
        "numeric_value": 5.52,
        "unit": "$ / BU",
        "location": "US TOTAL",
        "state_code": "US",
        "year": 2025,
        "short_desc": "WHEAT - PRICE RECEIVED, MEASURED IN $ / BU",
        "source": "WASDE",
        "imported_at": "2025-10-23T16:52:28.893365"
      }
    ]
  }
}
```

**Example Request**:
```bash
curl "http://localhost:8000/api/prices/search?commodity=WHEAT&sources=wasde&limit=10"
```

---

### Price Trends

Get price trend data for a commodity over a specified time period.

**Endpoint**: `GET /api/prices/trend/{commodity}`

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `commodity` | string | **Yes** | Commodity name (uppercase) |

**Query Parameters**:
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `period` | string | No | Time period (default: 1year) | `6months`, `1year`, `5years` |
| `location` | string | No | Geographic filter | `IOWA` |
| `source` | string | No | Data source (default: wasde) | `wasde` |

**Response**:
```json
{
  "commodity": "WHEAT",
  "period": "1year",
  "location": null,
  "source": "wasde",
  "data_points": 913,
  "data": [
    {
      "id": 145622,
      "commodity": "WHEAT",
      "statistic_category": "PRICE RECEIVED",
      "value": "5.3",
      "numeric_value": 5.3,
      "unit": "$ / BU",
      "location": "WASHINGTON",
      "state_code": "WA",
      "year": 2025,
      "short_desc": "WHEAT, WINTER - PRICE RECEIVED, MEASURED IN $ / BU",
      "source": "WASDE",
      "imported_at": "2025-10-23T16:52:33.208492"
    }
  ]
}
```

**Example Request**:
```bash
curl "http://localhost:8000/api/prices/trend/WHEAT?period=1year"
```

---

### Price Comparison

Compare commodity prices across different sources or years.

**Endpoint**: `GET /api/prices/compare/{commodity}`

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `commodity` | string | **Yes** | Commodity name (uppercase) |

**Query Parameters**:
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `year` | integer | No | Specific year to compare | `2025` |
| `sources` | string | No | Comma-separated sources | `wasde,fred` |
| `location` | string | No | Geographic filter | `US TOTAL` |

**Response**:
```json
{
  "commodity": "WHEAT",
  "sources_compared": ["wasde"],
  "year_filter": 2025,
  "comparison": {
    "wasde": {
      "count": 100,
      "sample": [
        {
          "id": 101709,
          "commodity": "WHEAT",
          "statistic_category": "PRICE RECEIVED",
          "value": "5.52",
          "numeric_value": 5.52,
          "unit": "$ / BU",
          "location": "US TOTAL",
          "state_code": "US",
          "year": 2025,
          "short_desc": "WHEAT - PRICE RECEIVED, MEASURED IN $ / BU",
          "source": "WASDE",
          "imported_at": "2025-10-23T16:52:28.893365"
        }
      ],
      "stats": {
        "commodity": "WHEAT",
        "count": 761,
        "min_price": 0.521,
        "max_price": 27.0,
        "avg_price": 5.78,
        "latest_year": 2025
      }
    }
  }
}
```

**Example Request**:
```bash
curl "http://localhost:8000/api/prices/compare/WHEAT?year=2025"
```

---

### Price Statistics

Get statistical summary for a commodity.

**Endpoint**: `GET /api/prices/stats/{commodity}`

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `commodity` | string | **Yes** | Commodity name (uppercase) |

**Query Parameters**:
| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `source` | string | No | Data source | `wasde` |

**Response**:
```json
{
  "commodity": "WHEAT",
  "source": "wasde",
  "statistics": {
    "commodity": "WHEAT",
    "count": 761,
    "min_price": 0.521,
    "max_price": 27.0,
    "avg_price": 5.78,
    "latest_year": 2025
  }
}
```

**Example Request**:
```bash
curl "http://localhost:8000/api/prices/stats/WHEAT"
```

---

### Database Statistics

Get overall database statistics including record counts and sync status.

**Endpoint**: `GET /api/prices/database/stats`

**Parameters**: None

**Response**:
```json
{
  "database_stats": {
    "wasde_data": 147369,
    "market_prices": 0,
    "economic_indicators": 0,
    "global_prices": 0,
    "retail_prices": 0,
    "total": 147369
  },
  "sync_status": [
    {
      "source": "WASDE",
      "last_sync": "2025-10-23T16:52:33.587004",
      "status": "SUCCESS",
      "records": 147369,
      "error": null
    },
    {
      "source": "USDA Market News",
      "last_sync": "2025-10-23T16:52:33.595449",
      "status": "FAILED",
      "records": 0,
      "error": "attempted relative import beyond top-level package"
    },
    {
      "source": "FRED",
      "last_sync": "2025-10-23T16:52:33.599394",
      "status": "FAILED",
      "records": 0,
      "error": "attempted relative import beyond top-level package"
    }
  ]
}
```

**Example Request**:
```bash
curl "http://localhost:8000/api/prices/database/stats"
```

---

## Data Models

### PriceRecord

```typescript
interface PriceRecord {
  id: number
  commodity: string
  statistic_category: string
  value: string
  numeric_value: number | null
  unit: string
  location: string
  state_code: string
  year: number
  short_desc: string
  source: string
  imported_at: string  // ISO 8601 timestamp
}
```

### PriceStatistics

```typescript
interface PriceStatistics {
  commodity: string
  count: number
  min_price: number
  max_price: number
  avg_price: number
  latest_year: number
}
```

### DatabaseStats

```typescript
interface DatabaseStats {
  database_stats: {
    wasde_data: number
    market_prices: number
    economic_indicators: number
    global_prices: number
    retail_prices: number
    total: number
  }
  sync_status: SyncStatus[]
}
```

### SyncStatus

```typescript
interface SyncStatus {
  source: string
  last_sync: string  // ISO 8601 timestamp
  status: 'SUCCESS' | 'FAILED' | 'PENDING'
  records: number
  error: string | null
}
```

---

## Error Handling

The API uses standard HTTP status codes:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Commodity or resource not found |
| 503 | Service Unavailable - Database not initialized |
| 500 | Internal Server Error |

**Error Response Format**:
```json
{
  "detail": "Error message describing what went wrong"
}
```

**Example Error**:
```json
{
  "detail": "Database not initialized"
}
```

---

## Rate Limits

Currently, no rate limits are enforced. This may change in future versions.

**Recommended Best Practices**:
- Limit parallel requests to 10 per second
- Use pagination with `limit` parameter for large datasets
- Cache responses when appropriate

---

## Examples

### Python

```python
import requests

# Search for wheat prices
response = requests.get(
    'http://localhost:8000/api/prices/search',
    params={
        'commodity': 'WHEAT',
        'sources': 'wasde',
        'limit': 10
    }
)
data = response.json()

# Get price statistics
stats_response = requests.get('http://localhost:8000/api/prices/stats/WHEAT')
stats = stats_response.json()

print(f"Average wheat price: ${stats['statistics']['avg_price']:.2f}")
```

### JavaScript

```javascript
// Search for wheat prices
const response = await fetch(
  'http://localhost:8000/api/prices/search?commodity=WHEAT&sources=wasde&limit=10'
)
const data = await response.json()

// Get price trends
const trendResponse = await fetch(
  'http://localhost:8000/api/prices/trend/WHEAT?period=1year'
)
const trends = await trendResponse.json()

console.log(`Found ${trends.data_points} data points`)
```

### cURL

```bash
# Search for corn prices in Iowa
curl "http://localhost:8000/api/prices/search?commodity=CORN&location=IOWA&limit=20"

# Get wheat price statistics
curl "http://localhost:8000/api/prices/stats/WHEAT"

# Get database statistics
curl "http://localhost:8000/api/prices/database/stats"

# Get price trends for soybeans
curl "http://localhost:8000/api/prices/trend/SOYBEANS?period=5years"

# Compare wheat prices across sources
curl "http://localhost:8000/api/prices/compare/WHEAT?year=2025"
```

---

## Supported Commodities

The database currently includes data for 35+ commodities:

**Grains & Oilseeds**:
- WHEAT (Winter, Spring, Durum)
- CORN
- SOYBEANS
- RICE
- BARLEY
- OATS
- SORGHUM

**Livestock & Dairy**:
- CATTLE
- HOGS
- CHICKEN
- EGGS
- MILK

**Other Commodities**:
- COTTON
- PEANUTS
- POTATOES
- And more...

To see the complete list:
```bash
curl "http://localhost:8000/api/wasde/commodities"
```

---

## Data Sources

| Source | Status | Update Frequency | Coverage |
|--------|--------|------------------|----------|
| USDA WASDE | ✅ Active | Monthly | US agricultural commodities |
| USDA Market News | ⏳ Pending | Daily | Terminal market prices |
| FRED | ⏳ Pending | Variable | Economic indicators |
| FAO | ⏳ Pending | Monthly | Global food prices |
| World Bank | ⏳ Pending | Monthly | International commodity prices |
| API Ninja | ⏳ Pending | Daily | Retail prices |

---

## Changelog

### Version 1.0 (October 23, 2025)
- Initial release
- WASDE data integration (147,369 records)
- 5 core API endpoints
- SQLite database backend
- Comprehensive statistics and trend analysis

---

## Support

For issues, questions, or feature requests:
- **Project**: Foodberg
- **Repository**: 
- **Documentation**: [README.md](database/README.md)

---

## License

API and database integration built for Foodberg project. Data sourced from public government and international organization databases.
