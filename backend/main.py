"""
Foodberg FastAPI Backend
Historical food price visualization API
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List, Optional, Dict, Any
import json
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
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
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
                "name": "World Bank Commodity Prices",
                "description": "Pink Sheet agricultural commodity prices",
                "indicators": ["Wheat", "Maize", "Rice", "Beef", "Sugar", "Coffee", "Cocoa"],
                "update_frequency": "Monthly",
                "api_key_required": False,
            },
        ]
    }


# ==================== PRICE ENDPOINTS ====================


@app.get("/api/prices/terminal/{market}")
async def get_terminal_prices(market: str, date: Optional[str] = None):
    """Get terminal market prices for a specific market"""
    usda_client = USDAMarketNewsClient()
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


@app.get("/api/wasde/{commodity}")
async def get_wasde_data(commodity: str, summary: bool = True):
    """Get WASDE data for a specific commodity from Robin canonical data store."""
    try:
        robin_client = RobinWASDEClient()
        if summary:
            data = robin_client.get_summary(commodity)
        else:
            data = robin_client.get_commodity_data(commodity)

        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No WASDE data found for commodity: {commodity}",
            )
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
