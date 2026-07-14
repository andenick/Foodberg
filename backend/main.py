"""
Foodberg FastAPI Backend
Historical food price visualization API
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List, Optional, Dict, Any
import json
import io
import csv
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os
import time
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import data source clients
from data_sources.fred_client import FREDClient
from data_sources.fao_client import FAOClient
from data_sources.worldbank_client import WorldBankClient
from data_sources.usda_client import USDAMarketNewsClient
from data_sources.robin_client import RobinWASDEClient
from database.manager import DatabaseManager


# =============================================================================
# SECURITY MIDDLEWARE
# =============================================================================


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting: 100 requests per minute per IP"""

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        now = time.time()
        minute_ago = now - 60
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > minute_ago
        ]

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {self.requests_per_minute} requests per minute",
                    "retry_after": 60,
                },
            )

        self.requests[client_ip].append(now)
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """OWASP security headers"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https://api.stlouisfed.org https://api.bls.gov https://api.worldbank.org"
        )
        if os.getenv("ENV") == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        # Deny-by-default for every client resource. An educational data site
        # never needs the user's hardware, location, storage, clipboard or a
        # notification channel (EDUCATIONAL_DISCLAIMER_STANDARD, client-resources
        # rule). The SPA web server (Caddy) ships the same header for static
        # assets; this is the API-side backstop.
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), notifications=(), "
            "persistent-storage=(), clipboard-read=(), payment=(), usb=()"
        )
        return response


# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="Foodberg API",
    description="Historical food price visualization API",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENV") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENV") != "production" else None,
)

app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
app.add_middleware(SecurityHeadersMiddleware)

# Carson Telemetry Standard v1.0 (Layer 2) — one usage_events row per request.
# Wrapped so a missing/broken telemetry package can never block API startup.
try:
    from carson_telemetry import telemetry

    app.add_middleware(telemetry.ASGIMiddleware, service="foodberg")
except ImportError:
    pass

allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]
if os.getenv("ENV") == "production":
    prod_origins = os.getenv("CORS_ORIGINS", "")
    allowed_origins = [o.strip() for o in prod_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)


# ==================== HEALTH & STATUS ====================


@app.get("/")
async def root():
    return {
        "service": "Foodberg API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "operational",
            "database": "operational",
        },
    }


@app.get("/api/data/status")
async def get_data_status():
    """Get freshness status of all data sources"""
    import sqlite3

    db_path = Path(__file__).parent / "data" / "foodberg.db"
    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": {
            "exists": db_path.exists(),
            "size_mb": (
                round(db_path.stat().st_size / (1024 * 1024), 2)
                if db_path.exists()
                else 0
            ),
        },
        "sources": {},
    }

    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            tables_info = {
                "wasde_psd": {"name": "WASDE Supply & Demand (USDA FAS PS&D)", "date_col": "market_year"},
                "wasde_data": {"name": "WASDE (USDA)", "date_col": "year"},
                "economic_indicators": {
                    "name": "Economic Indicators (FRED/BLS)",
                    "date_col": "date",
                },
                "global_prices": {
                    "name": "Global Prices (FAO/World Bank)",
                    "date_col": "date",
                },
                "retail_prices": {
                    "name": "Retail Prices",
                    "date_col": "date",
                },
                "composite_indices": {
                    "name": "Composite Food Indices",
                    "date_col": "date",
                },
            }

            for table, info in tables_info.items():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]

                    cursor.execute(
                        f"SELECT MIN({info['date_col']}), MAX({info['date_col']}) FROM {table}"
                    )
                    min_date, max_date = cursor.fetchone()

                    freshness = "unknown"
                    if max_date:
                        try:
                            if "T" in str(max_date):
                                last_date = datetime.fromisoformat(
                                    max_date.replace("Z", "+00:00")
                                )
                            else:
                                last_date = datetime.strptime(
                                    str(max_date)[:10], "%Y-%m-%d"
                                )
                            days_old = (
                                datetime.now() - last_date.replace(tzinfo=None)
                            ).days
                            if days_old < 7:
                                freshness = "fresh"
                            elif days_old < 30:
                                freshness = "recent"
                            elif days_old < 90:
                                freshness = "stale"
                            else:
                                freshness = "outdated"
                        except:
                            freshness = "unknown"

                    status["sources"][table] = {
                        "name": info["name"],
                        "records": count,
                        "date_range": {"min": min_date, "max": max_date},
                        "freshness": freshness,
                    }
                except Exception as e:
                    status["sources"][table] = {"name": info["name"], "error": str(e)}

            conn.close()
        except Exception as e:
            status["error"] = str(e)

    return status


@app.post("/api/data/reindex")
async def reindex_data():
    """Rebuild composite food-price indices from the underlying source tables.

    Reads raw FAO sub-indices and BLS CPI components from the database, then
    recomputes every composite index (FAO overall, BLS overall, plus the
    individual FAO categories) with their documented weights. A read-only
    operation on source data; the composite_indices table is the only target
    of writes.
    """
    try:
        # Rebuild both index families from the composite module.
        from indices.composite import compute_all_indices
        db_path = str(Path(__file__).parent / "data" / "foodberg.db")
        if not Path(db_path).exists():
            raise HTTPException(status_code=503, detail="Database file not found")
        total = compute_all_indices(db_path=db_path)
        return {
            "status": "ok",
            "message": f"Rebuilt {total} composite index records.",
            "total": total,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data/sources")
async def get_data_sources():
    """List all available data sources and their capabilities"""
    return {
        "sources": [
            {
                "id": "wasde",
                "name": "USDA WASDE Reports",
                "description": "World Agricultural Supply and Demand Estimates - 50 commodities",
                "indicators": ["Grains", "Oilseeds", "Livestock", "Dairy", "Fruits", "Nuts"],
                "update_frequency": "Monthly",
                "api_key_required": False,
            },
            {
                "id": "fred",
                "name": "Federal Reserve Economic Data",
                "description": "CPI food components, PPI, average food prices",
                "indicators": [
                    "CPI Food at Home",
                    "CPI Food Away",
                    "CPI Cereals & Bakery",
                    "CPI Meats/Poultry/Fish/Eggs",
                    "CPI Fruits & Vegetables",
                    "PPI Farm Products",
                    "PPI Processed Foods",
                    "Average Prices (eggs, bread, milk, beef, chicken)",
                ],
                "update_frequency": "Monthly",
                "api_key_required": True,
            },
            {
                "id": "bls",
                "name": "Bureau of Labor Statistics",
                "description": "Consumer Price Index food sub-components",
                "indicators": ["CPI Food at Home", "CPI Food Away from Home"],
                "update_frequency": "Monthly",
                "api_key_required": False,
            },
            {
                "id": "fao",
                "name": "FAO Food Price Index",
                "description": "Global food commodity price indices",
                "indicators": ["Meat", "Dairy", "Cereals", "Vegetable Oils", "Sugar"],
                "update_frequency": "Monthly",
                "api_key_required": False,
            },
            {
                "id": "worldbank",
                "name": "World Bank Development Indicators",
                "description": "Agriculture & food indicators per region (production, yield, trade shares)",
                "indicators": ["Cereal Production", "Cereal Yield", "Food Production Index",
                               "Food Imports/Exports %", "Ag Value Added"],
                "update_frequency": "Annual",
                "api_key_required": False,
            },
            {
                "id": "nass_history",
                "name": "USDA NASS Historical Prices",
                "description": "Farm-gate prices received, production & yield — national to 1908, state to 1950",
                "indicators": ["Prices Received", "Production", "Yield",
                               "50 commodities", "National + state"],
                "update_frequency": "Annual + Monthly",
                "api_key_required": False,
            },
            {
                "id": "faostat",
                "name": "FAOSTAT Producer Prices & Food CPIs",
                "description": "Producer prices (USD/tonne) per country & food item, plus per-country consumer food price indices",
                "indicators": ["Producer Prices (USD/t)", "~160 countries",
                               "Food CPI (2015=100)", "Monthly CPI"],
                "update_frequency": "Annual / Monthly",
                "api_key_required": False,
            },
            {
                "id": "pinksheet",
                "name": "World Bank Pink Sheet",
                "description": "Monthly global commodity prices & index families, 1960-present",
                "indicators": ["~45 commodities", "Food index", "Beverages index",
                               "Agriculture index", "Monthly since 1960"],
                "update_frequency": "Monthly",
                "api_key_required": False,
            },
            {
                "id": "blsap",
                "name": "BLS Average Retail Prices",
                "description": "US city-average retail prices for ~50 food products (eggs, milk, bread, beef...)",
                "indicators": ["Retail $ per unit", "US city average",
                               "Monthly since 1980"],
                "update_frequency": "Monthly",
                "api_key_required": False,
            },
        ]
    }


# ==================== PRICE ENDPOINTS ====================


@app.get("/api/prices/terminal/{market}")
async def get_terminal_prices(market: str, date: Optional[str] = None):
    """Get terminal market prices for a specific market (requires USDA_API_KEY)"""
    try:
        usda_client = USDAMarketNewsClient()
    except ValueError:
        raise HTTPException(
            status_code=503,
            detail="USDA Market News API key not configured. Set USDA_API_KEY environment variable.",
        )
    data = usda_client.get_terminal_market_prices(market)
    if data:
        return data
    return {"error": f"Could not retrieve data for market: {market}"}


@app.get("/api/prices/search")
async def search_prices(
    commodity: str,
    sources: str = "wasde",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 100,
):
    """Unified price search across all data sources"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        source_list = [s.strip() for s in sources.split(",")]
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        results = db_manager.search_prices(
            commodity=commodity,
            sources=source_list,
            start_date=start_dt,
            end_date=end_dt,
            location=location,
            limit=limit,
        )

        return {
            "commodity": commodity,
            "sources": source_list,
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "location": location,
            },
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/trend/{commodity}")
async def get_price_trend(
    commodity: str,
    period: str = "6months",
    location: Optional[str] = None,
    source: str = "wasde",
):
    """Get price trend data for a commodity"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        period_days = {
            "1month": 30,
            "3months": 90,
            "6months": 180,
            "1year": 365,
            "2years": 730,
            "5years": 1825,
            "all": 36500,
        }
        days = period_days.get(period, 180)
        start_date = datetime.now() - timedelta(days=days)

        if source == "wasde":
            prices = db_manager.get_wasde_prices(
                commodity=commodity,
                location=location,
                start_year=start_date.year,
                end_year=datetime.now().year,
                limit=1000,
            )
        else:
            prices = []

        return {
            "commodity": commodity,
            "period": period,
            "location": location,
            "source": source,
            "data_points": len(prices),
            "data": prices,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/compare/{commodity}")
async def compare_prices(
    commodity: str, sources: str = "wasde", year: Optional[int] = None
):
    """Compare prices across multiple data sources"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        source_list = [s.strip() for s in sources.split(",")]
        comparison = {}

        for source in source_list:
            if source == "wasde":
                prices = db_manager.get_wasde_prices(
                    commodity=commodity, year=year, limit=100
                )
                if prices:
                    comparison["wasde"] = {
                        "count": len(prices),
                        "sample": prices[:10],
                        "stats": db_manager.get_wasde_statistics(commodity),
                    }

        return {
            "commodity": commodity,
            "sources_compared": list(comparison.keys()),
            "year_filter": year,
            "comparison": comparison,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/stats/{commodity}")
async def get_price_statistics(commodity: str, source: str = "wasde"):
    """Get statistical summary of commodity prices"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        if source == "wasde":
            stats = db_manager.get_wasde_statistics(commodity)
        else:
            stats = {}
        return {"commodity": commodity, "source": source, "statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/history/{commodity}")
async def get_price_history(commodity: str):
    """
    Real historical monthly price series for a commodity.

    Backed by global_prices (Alpha Vantage spot-price series, 1992-present)
    for the commodities that have genuine monthly history:
    wheat, corn (maize), coffee, sugar, cotton.

    For any other commodity there is NO real price-history series in the local
    data, so an empty series is returned with has_history=False and a note.
    No synthetic, interpolated, or placeholder values are ever generated.
    """
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        series = db_manager.get_commodity_price_history(commodity)
        if series:
            return {
                "commodity": commodity.lower(),
                "has_history": True,
                "source": "Alpha Vantage (global commodity spot prices)",
                "unit": series[0].get("unit"),
                "currency": series[0].get("currency"),
                "data_points": len(series),
                "date_range": {
                    "start": series[0]["date"],
                    "end": series[-1]["date"],
                },
                "data": series,
            }
        return {
            "commodity": commodity.lower(),
            "has_history": False,
            "source": None,
            "data_points": 0,
            "data": [],
            "note": (
                "No historical price series available for this commodity in the "
                "local dataset. Real monthly history is available for: wheat, corn, "
                "coffee, sugar, cotton."
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/database/stats")
async def get_database_stats():
    """Get overall database statistics"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        stats = db_manager.get_database_stats()
        sync_status = db_manager.get_sync_status()
        return {"database_stats": stats, "sync_status": sync_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WASDE ENDPOINTS (Robin Integration) ====================


@app.get("/api/wasde/commodities")
async def get_wasde_commodities():
    """Get list of available WASDE commodities from Robin data store"""
    try:
        robin_client = RobinWASDEClient()
        commodities = robin_client.get_available_commodities()
        return {
            "source": "Robin Council Tool - USDA NASS WASDE Data",
            "commodities": commodities,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _csv_response(records: List[Dict[str, Any]], filename: str) -> StreamingResponse:
    """Serialize a list of dict rows to a downloadable text/csv StreamingResponse.

    Uses the union of all keys as the header (some sources return ragged rows).
    Always returns at least a header line so the file is never empty/ambiguous.
    """
    cols: List[str] = []
    seen = set()
    for r in records:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                cols.append(k)
    if not cols:
        cols = ["note"]
        records = [{"note": "No data available for this query."}]

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    for r in records:
        writer.writerow(r)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )


@app.get("/api/wasde/{commodity}.csv")
async def get_wasde_data_csv(commodity: str, limit: int = 5000):
    """CSV export of the per-commodity WASDE / price series (same data as the
    JSON endpoint, served as a downloadable text/csv attachment). Registered
    BEFORE the generic /api/wasde/{commodity} route so the `.csv` suffix wins."""
    payload = await get_wasde_data(commodity, limit)
    records = payload.get("data", []) if isinstance(payload, dict) else []
    return _csv_response(records, f"{commodity.lower()}_wasde")


@app.get("/api/wasde/{commodity}")
async def get_wasde_data(commodity: str, limit: int = 5000):
    """
    Per-commodity price series for the Price Explorer chart.

    For commodities with a genuine historical monthly price series in the local
    data (wheat, corn/maize, coffee, sugar, cotton — Alpha Vantage spot prices,
    1992-present) this returns that REAL series, shaped so each row carries
    `year` + `numeric_value` for the time-series chart.

    For all other commodities it returns the local WASDE records as before. The
    local WASDE table holds a single marketing year only (no time series), so
    those commodities legitimately show what real data exists, labeled via the
    `has_history` flag. No synthetic or interpolated values are ever produced.
    """
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        # Prefer the real historical price series where one exists.
        history = db_manager.get_commodity_price_history(commodity)
        if history:
            records = [
                {
                    "commodity": commodity.upper(),
                    "statistic_category": "PRICE, SPOT",
                    "value": str(row["price"]),
                    "numeric_value": row["price"],
                    "unit": row.get("unit"),
                    "location": "GLOBAL",
                    "year": row["year"],
                    "date": row["date"],
                    "source": row.get("source") or "Alpha Vantage",
                }
                for row in history
            ]
            return {
                "commodity": commodity.upper(),
                "source": "Alpha Vantage (global commodity spot prices)",
                "has_history": True,
                "data_points": len(records),
                "date_range": {
                    "start": history[0]["date"],
                    "end": history[-1]["date"],
                },
                "data": records,
            }

        # Fallback: local WASDE records (single marketing year; no time series).
        session = db_manager.get_session()
        try:
            from database.models import WASDEData
            from sqlalchemy import desc
            query = session.query(WASDEData).filter(
                WASDEData.commodity == commodity.upper()
            ).order_by(desc(WASDEData.year)).limit(limit)
            results = query.all()
            records = [db_manager._wasde_to_dict(r) for r in results]
        finally:
            session.close()

        return {
            "commodity": commodity.upper(),
            "source": "USDA NASS (via Robin)",
            "has_history": False,
            "data_points": len(records),
            "data": records,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wasde/{commodity}/national")
async def get_wasde_national(commodity: str):
    """Get national-level (US TOTAL) WASDE data for a commodity"""
    try:
        robin_client = RobinWASDEClient()
        data = robin_client.get_national_data(commodity)

        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No national WASDE data found for commodity: {commodity}",
            )
        return {
            "commodity": commodity,
            "level": "national",
            "data_points": len(data),
            "data": data,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wasde/{commodity}/state/{state}")
async def get_wasde_state(commodity: str, state: str):
    """Get state-level WASDE data for a commodity"""
    try:
        robin_client = RobinWASDEClient()
        data = robin_client.get_state_data(commodity, state)

        if not data or len(data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No WASDE data found for {commodity} in {state}",
            )
        return {
            "commodity": commodity,
            "state": state.upper(),
            "data_points": len(data),
            "data": data,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ECONOMIC INDICATORS ====================


@app.get("/api/economic/indicators")
async def get_economic_indicators():
    """Get FRED economic indicators (CPI, PPI, food prices)"""
    client = FREDClient()
    indicators = await client.get_all_indicators()
    return indicators


@app.get("/api/global/fao-index")
async def get_fao_index(category: str = "overall"):
    """Get FAO Food Price Index"""
    client = FAOClient()
    if category == "all":
        indices = await client.get_all_indices()
        return indices
    else:
        index = await client.get_food_price_index(category)
        return {
            "category": category,
            "data": index,
            "timestamp": datetime.now().isoformat(),
        }


@app.get("/api/geo/indicators")
async def get_geo_indicators():
    """World Bank development indicators with per-region annual coverage —
    the real multi-country data behind the Geographic page."""
    client = WorldBankClient()
    return {"indicators": client.get_geo_indicators()}


@app.get("/api/geo/producer/items")
async def get_producer_items(min_countries: int = 5):
    """FAOSTAT items with per-country producer-price coverage (USD/tonne)."""
    client = WorldBankClient()
    return {"items": client.get_producer_price_items(min_countries)}


@app.get("/api/geo/producer/{item}")
async def get_producer_series(item: str):
    """Per-country annual producer-price series for one FAOSTAT item."""
    client = WorldBankClient()
    return client.get_producer_price_series(item)


@app.get("/api/geo/states/{commodity}")
async def get_state_series(commodity: str):
    """USDA NASS state-level farm-gate price series for one commodity."""
    client = WorldBankClient()
    return client.get_state_price_series(commodity)


@app.get("/api/geo/{indicator_code}")
async def get_geo_series(indicator_code: str):
    """All (region, year, value) rows for one World Bank indicator."""
    client = WorldBankClient()
    return client.get_geo_series(indicator_code)


@app.get("/api/prices/coverage")
async def get_price_coverage():
    """Multi-source per-commodity price-history coverage (honest UI labels)."""
    client = WorldBankClient()
    return client.get_price_coverage()


@app.get("/api/prices/source/{commodity}")
async def get_source_history_endpoint(commodity: str, source: str = "nass"):
    """One commodity's series from a chosen source: nass | pinksheet | retail.
    (Alpha Vantage series stay on /api/prices/history/{commodity}.)"""
    client = WorldBankClient()
    return client.get_source_history(commodity, source)


@app.get("/api/indices/global")
async def get_global_indices():
    """Pink Sheet index series + FAO per-country food-CPI catalog."""
    client = WorldBankClient()
    return client.get_global_indices()


@app.get("/api/indices/cpi/{country}")
async def get_country_cpi(country: str):
    """One country's monthly FAO food CPI (2015=100)."""
    client = WorldBankClient()
    return client.get_country_cpi_series(country)


@app.get("/api/indices/pinksheet/{series}")
async def get_pinksheet_series_endpoint(series: str):
    """One World Bank Pink Sheet monthly series (commodity or index)."""
    client = WorldBankClient()
    return client.get_pinksheet_series(series)


@app.get("/api/global/worldbank/{commodity}")
async def get_worldbank_commodity(commodity: str):
    """Get World Bank commodity price data"""
    client = WorldBankClient()
    data = await client.get_commodity_price(commodity)
    return data


@app.get("/api/global/worldbank/multiple")
async def get_worldbank_multiple(commodities: str):
    """Get World Bank data for multiple commodities (comma-separated)"""
    commodity_list = [c.strip() for c in commodities.split(",")]
    client = WorldBankClient()
    data = await client.get_multiple_commodities(commodity_list)
    return data


# ==================== COMPOSITE INDICES ====================


@app.get("/api/indices/")
async def get_composite_indices():
    """Get all composite food price indices with latest values"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        indices = db_manager.get_composite_indices()
        return {"indices": indices, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/indices/{category}.csv")
async def get_composite_index_csv(category: str):
    """CSV export of a composite food-price index's full history (downloadable
    attachment). Registered before the generic /api/indices/{category} route."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        data = db_manager.get_composite_index_history(category)
        return _csv_response(data or [], f"{category}_index")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/indices/{category}")
async def get_composite_index(category: str):
    """Get historical values for a specific composite index category"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        data = db_manager.get_composite_index_history(category)
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No index data for category: {category}",
            )
        return {
            "category": category,
            "data_points": len(data),
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        # Propagate the honest 404 (unknown category, e.g. "global") instead of
        # masking it as a 500 in the generic handler below (FBD-1 tail).
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== BULK DATASET DOWNLOADS ====================
#
# Mandate: "None of the data is available or hosted on this site." Users expect
# to download the underlying data, not just query it. These endpoints serve the
# backend's real datasets as full CSV + Parquet files, plus a data dictionary,
# all streamed from the existing foodberg.db via the DatabaseManager / direct
# SQL. No synthetic data: every row is a real DB row. Educational disclaimer is
# carried in the data dictionary and the downloads README (see frontend).

# Catalog of downloadable datasets. Each entry names the DB table it streams
# from, the upstream authority to defer to, and a short description. The id is
# what appears in the /api/download/{id}.{csv|parquet} path.
DOWNLOAD_DATASETS: List[Dict[str, Any]] = [
    {
        "id": "wasde",
        "name": "USDA WASDE — supply & demand estimates",
        "table": "wasde_data",
        "source": "USDA NASS / WASDE",
        "defer_to": "USDA (usda.gov/oce/commodity/wasde)",
        "description": (
            "World Agricultural Supply and Demand Estimates: per-commodity "
            "statistics (production, price received, stocks) by year, location "
            "and statistic category."
        ),
        "order_by": "commodity, year",
    },
    {
        "id": "price_history",
        "name": "Commodity price history (global spot prices)",
        "table": "global_prices",
        "source": "Alpha Vantage / FAO / World Bank (via global_prices)",
        "defer_to": "the named upstream source in each row's `source` column",
        "description": (
            "Monthly global commodity spot prices and indices, including the "
            "Alpha Vantage history series (wheat, corn, coffee, sugar, cotton, "
            "1992-present) and FAO / World Bank global price rows."
        ),
        "order_by": "commodity, date",
    },
    {
        "id": "fao_food_price_index",
        "name": "FAO Food Price Index",
        "table": "composite_indices",
        "source": "FAO Food Price Index (fao_* categories)",
        "defer_to": "FAO (fao.org/worldfoodsituation/foodpricesindex)",
        "description": (
            "FAO Food Price Index monthly series by category (overall, cereals, "
            "dairy, meat, vegetable oils, sugar), as computed composite indices."
        ),
        "where": "category LIKE 'fao_%'",
        "order_by": "category, date",
    },
    {
        "id": "economic_indicators",
        "name": "Economic indicators (FRED / BLS)",
        "table": "economic_indicators",
        "source": "FRED (St. Louis Fed) & BLS",
        "defer_to": "FRED (fred.stlouisfed.org) / BLS (bls.gov)",
        "description": (
            "Food-related CPI / PPI and macro indicators (food CPI, inflation, "
            "employment, output, interest rates) by date, series and category."
        ),
        "order_by": "category, indicator_name, date",
    },
]

_DOWNLOAD_INDEX = {d["id"]: d for d in DOWNLOAD_DATASETS}


def _download_db_path() -> Path:
    return Path(__file__).parent / "data" / "foodberg.db"


def _load_dataset_df(dataset_id: str):
    """Load a download dataset as a pandas DataFrame straight from foodberg.db.

    Returns the DataFrame. Raises HTTPException(404) for an unknown id and
    HTTPException(503) when the database file is missing. Reads via sqlite3 so a
    full-table export is a single streamed query (the DatabaseManager ORM paths
    are capped/limited and meant for the interactive UI, not bulk export)."""
    import sqlite3
    import pandas as pd

    spec = _DOWNLOAD_INDEX.get(dataset_id)
    if not spec:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown dataset '{dataset_id}'. See /api/download/datasets.",
        )

    db_path = _download_db_path()
    if not db_path.exists():
        raise HTTPException(status_code=503, detail="Database file not found")

    table = spec["table"]
    where = spec.get("where")
    order_by = spec.get("order_by")
    sql = f"SELECT * FROM {table}"
    if where:
        sql += f" WHERE {where}"
    if order_by:
        sql += f" ORDER BY {order_by}"

    conn = sqlite3.connect(str(db_path))
    try:
        df = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    # Drop the internal autoincrement id; it carries no analytical meaning.
    if "id" in df.columns:
        df = df.drop(columns=["id"])
    return df


@app.get("/api/download/datasets")
async def list_download_datasets():
    """Catalog of downloadable datasets (one card per entry in the UI).

    Reports the real row count and date/year span for each dataset so the
    Downloads page can show genuine sizes. Falls back gracefully if the DB is
    unavailable (counts reported as null rather than failing the catalog)."""
    import sqlite3

    db_path = _download_db_path()
    out = []
    conn = None
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
        except Exception:
            conn = None

    for spec in DOWNLOAD_DATASETS:
        entry = {
            "id": spec["id"],
            "name": spec["name"],
            "description": spec["description"],
            "source": spec["source"],
            "defer_to": spec["defer_to"],
            "formats": ["csv", "parquet"],
            "csv_url": f"/api/download/{spec['id']}.csv",
            "parquet_url": f"/api/download/{spec['id']}.parquet",
            "rows": None,
        }
        if conn is not None:
            try:
                where = f" WHERE {spec['where']}" if spec.get("where") else ""
                cur = conn.cursor()
                cur.execute(f"SELECT COUNT(*) FROM {spec['table']}{where}")
                entry["rows"] = cur.fetchone()[0]
            except Exception:
                entry["rows"] = None
        out.append(entry)
    if conn is not None:
        conn.close()

    return {
        "datasets": out,
        "dictionary_url": "/api/download/dictionary.csv",
        "disclaimer": (
            "The data on this site is reconstructed/aggregated for research "
            "transparency and education. It may lag official revisions or "
            "contain reconstruction error, and it is not a substitute for the "
            "original source. For authoritative figures, defer to the named "
            "original source for each dataset (USDA, FAO, FRED/BLS, World Bank)."
        ),
    }


@app.get("/api/download/dictionary.csv")
async def download_data_dictionary():
    """Data dictionary across all downloadable datasets, as a CSV attachment.

    Header carries the educational disclaimer; each row documents one column of
    one dataset (dataset id, source authority, column name, dtype)."""
    import sqlite3

    rows: List[Dict[str, Any]] = []
    db_path = _download_db_path()
    conn = sqlite3.connect(str(db_path)) if db_path.exists() else None
    for spec in DOWNLOAD_DATASETS:
        cols: List[tuple] = []
        if conn is not None:
            try:
                cur = conn.cursor()
                cur.execute(f"PRAGMA table_info({spec['table']})")
                cols = [(r[1], r[2]) for r in cur.fetchall() if r[1] != "id"]
            except Exception:
                cols = []
        for col_name, col_type in cols:
            rows.append(
                {
                    "dataset": spec["id"],
                    "dataset_name": spec["name"],
                    "source": spec["source"],
                    "defer_to": spec["defer_to"],
                    "column": col_name,
                    "type": col_type or "TEXT",
                }
            )
    if conn is not None:
        conn.close()

    # Prepend the disclaimer as a leading comment-style row so it travels with
    # the dictionary off-site (per EDUCATIONAL_DISCLAIMER_STANDARD).
    header_note = {
        "dataset": "# DISCLAIMER",
        "dataset_name": (
            "Data reconstructed/aggregated for research & education; may lag "
            "official revisions or contain error. Not a substitute for the "
            "original source. Defer to each dataset's named authority."
        ),
        "source": "",
        "defer_to": "",
        "column": "",
        "type": "",
    }
    return _csv_response([header_note] + rows, "foodberg_data_dictionary")


@app.get("/api/download/{dataset}.csv")
async def download_dataset_csv(dataset: str):
    """Full CSV export of a dataset, streamed from foodberg.db."""
    df = _load_dataset_df(dataset)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="foodberg_{dataset}.csv"'
        },
    )


@app.get("/api/download/{dataset}.parquet")
async def download_dataset_parquet(dataset: str):
    """Full Parquet export of a dataset (pandas + pyarrow), streamed from the DB."""
    df = _load_dataset_df(dataset)
    buf = io.BytesIO()
    df.to_parquet(buf, index=False, engine="pyarrow")
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/vnd.apache.parquet",
        headers={
            "Content-Disposition": f'attachment; filename="foodberg_{dataset}.parquet"'
        },
    )


# ==================== WASDE / PS&D SUPPLY & DEMAND (multi-year balance sheets) ====================
# Source: USDA FAS PS&D (Production, Supply & Distribution) bulk CSVs, Market_Year
# 1960-present. This is the canonical machine-readable supply/demand database
# underlying the WASDE world tables and "incorporates all historical revisions".
# Table `wasde_psd` is loaded by Technical/data_processors/process_psd_wasde.py.

_PSD_DB = Path(__file__).parent / "data" / "foodberg.db"


def _psd_conn():
    import sqlite3
    conn = sqlite3.connect(str(_PSD_DB))
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/api/psd/commodities")
async def psd_commodities():
    """List PS&D commodities with their region coverage and marketing-year span."""
    try:
        conn = _psd_conn()
        rows = conn.execute(
            """
            SELECT commodity,
                   COUNT(DISTINCT country) AS countries,
                   MIN(market_year) AS min_year,
                   MAX(market_year) AS max_year,
                   COUNT(*) AS rows
            FROM wasde_psd
            WHERE country IN ('United States', 'World')
            GROUP BY commodity
            ORDER BY commodity
            """
        ).fetchall()
        conn.close()
        return {
            "source": "USDA FAS PS&D (Production, Supply & Distribution)",
            "source_url": "https://apps.fas.usda.gov/psdonline/downloads/",
            "regions": ["United States", "World"],
            "count": len(rows),
            "commodities": [dict(r) for r in rows],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/psd/{commodity}/attributes")
async def psd_attributes(commodity: str, region: str = "World"):
    """List the balance-sheet line items available for a commodity x region."""
    try:
        conn = _psd_conn()
        rows = conn.execute(
            """
            SELECT attribute, unit,
                   MIN(market_year) AS min_year,
                   MAX(market_year) AS max_year,
                   COUNT(*) AS n_years,
                   MAX(is_aggregate) AS is_aggregate
            FROM wasde_psd
            WHERE commodity = ? AND country = ?
            GROUP BY attribute, unit
            HAVING COUNT(*) >= 2
            ORDER BY attribute
            """,
            (commodity, region),
        ).fetchall()
        conn.close()
        if not rows:
            raise HTTPException(status_code=404, detail=f"No PS&D series for {commodity} / {region}")
        return {
            "commodity": commodity,
            "region": region,
            "attributes": [dict(r) for r in rows],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/psd/{commodity}/series")
async def psd_series(commodity: str, attribute: str, region: str = "World"):
    """
    Return a single balance-sheet line item as a multi-year series
    (one value per marketing year) for charting. Honest: missing years absent.
    """
    try:
        conn = _psd_conn()
        rows = conn.execute(
            """
            SELECT market_year AS year, value, unit, is_aggregate, n_countries
            FROM wasde_psd
            WHERE commodity = ? AND country = ? AND attribute = ?
            ORDER BY market_year
            """,
            (commodity, region, attribute),
        ).fetchall()
        meta = conn.execute(
            "SELECT DISTINCT source, source_url FROM wasde_psd WHERE commodity = ? LIMIT 1",
            (commodity,),
        ).fetchone()
        conn.close()
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No PS&D series for {commodity} / {region} / {attribute}",
            )
        unit = rows[0]["unit"]
        is_agg = bool(rows[0]["is_aggregate"])
        return {
            "commodity": commodity,
            "region": region,
            "attribute": attribute,
            "unit": unit,
            "is_aggregate": is_agg,
            "note": (
                "World = sum of reported countries (additive attributes only)"
                if is_agg else None
            ),
            "source": meta["source"] if meta else None,
            "source_url": meta["source_url"] if meta else None,
            "n_years": len(rows),
            "year_range": {"start": rows[0]["year"], "end": rows[-1]["year"]},
            "data": [
                {"year": r["year"], "value": r["value"], "unit": r["unit"]}
                for r in rows
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/psd/{commodity}/balance-sheet")
async def psd_balance_sheet(commodity: str, region: str = "World", year: Optional[int] = None):
    """
    Full balance sheet (all line items) for a commodity x region at a given
    marketing year (defaults to the latest available year).
    """
    try:
        conn = _psd_conn()
        if year is None:
            yr = conn.execute(
                "SELECT MAX(market_year) FROM wasde_psd WHERE commodity = ? AND country = ?",
                (commodity, region),
            ).fetchone()[0]
        else:
            yr = year
        rows = conn.execute(
            """
            SELECT attribute, value, unit, is_aggregate
            FROM wasde_psd
            WHERE commodity = ? AND country = ? AND market_year = ?
            ORDER BY attribute
            """,
            (commodity, region, yr),
        ).fetchall()
        conn.close()
        if not rows:
            raise HTTPException(status_code=404, detail=f"No PS&D balance sheet for {commodity} / {region} / {yr}")
        return {
            "commodity": commodity,
            "region": region,
            "market_year": yr,
            "line_items": [dict(r) for r in rows],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STARTUP & SHUTDOWN ====================

db_manager = None


@app.on_event("startup")
async def startup_event():
    global db_manager
    print("Foodberg API starting up...")
    try:
        db_manager = DatabaseManager()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    print("Foodberg API shutting down...")


# --- PS&D WASDE Supply & Demand (additive; see routers/psd_router.py) ---
# Reconciled 2026-07-14 (CDF campaign): the live box image carried this mount
# additively (2026-06-21) while the repo/deploy tree carried the /api/indices/global
# and /api/geo/producer/items routes. This canonical main.py carries BOTH surfaces.
from routers.psd_router import router as psd_router
app.include_router(psd_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
