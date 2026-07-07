"""
psd_router.py — WASDE Supply & Demand (USDA FAS PS&D) endpoints.

Self-contained APIRouter so it can be mounted on the deployed backend WITHOUT
overwriting main.py (the box's live main.py has diverged from the repo and adds
/api/prices/coverage etc. — DO NOT clobber it). To wire on the box:

    from routers.psd_router import router as psd_router
    app.include_router(psd_router)

Reads the `wasde_psd` table (loaded by Technical/data_processors/process_psd_wasde.py)
from the same SQLite file the rest of the backend uses.

Source: USDA FAS PS&D (Production, Supply & Distribution), Market_Year 1960→present.
This is the machine-readable supply/demand database underlying the WASDE world
tables; it incorporates all historical revisions. Honest: missing years stay
missing; World totals are the sum of reported countries for additive attributes only.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/psd", tags=["wasde-psd"])

# Same DB the backend uses (backend/data/foodberg.db).
_DB = Path(__file__).resolve().parent.parent / "data" / "foodberg.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB))
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/commodities")
def psd_commodities():
    """PS&D commodities with region coverage and marketing-year span."""
    try:
        conn = _conn()
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


@router.get("/{commodity}/attributes")
def psd_attributes(commodity: str, region: str = "World"):
    """Balance-sheet line items available for a commodity x region (>=2 years)."""
    try:
        conn = _conn()
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
        return {"commodity": commodity, "region": region,
                "attributes": [dict(r) for r in rows]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{commodity}/series")
def psd_series(commodity: str, attribute: str, region: str = "World"):
    """One balance-sheet line item as a multi-year series (one value per MY)."""
    try:
        conn = _conn()
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
            raise HTTPException(status_code=404,
                                detail=f"No PS&D series for {commodity} / {region} / {attribute}")
        is_agg = bool(rows[0]["is_aggregate"])
        return {
            "commodity": commodity, "region": region, "attribute": attribute,
            "unit": rows[0]["unit"], "is_aggregate": is_agg,
            "note": ("World = sum of reported countries (additive attributes only)"
                     if is_agg else None),
            "source": meta["source"] if meta else None,
            "source_url": meta["source_url"] if meta else None,
            "n_years": len(rows),
            "year_range": {"start": rows[0]["year"], "end": rows[-1]["year"]},
            "data": [{"year": r["year"], "value": r["value"], "unit": r["unit"]} for r in rows],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{commodity}/balance-sheet")
def psd_balance_sheet(commodity: str, region: str = "World", year: Optional[int] = None):
    """Full balance sheet (all line items) at a marketing year (default latest)."""
    try:
        conn = _conn()
        yr = year
        if yr is None:
            yr = conn.execute(
                "SELECT MAX(market_year) FROM wasde_psd WHERE commodity = ? AND country = ?",
                (commodity, region),
            ).fetchone()[0]
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
            raise HTTPException(status_code=404,
                                detail=f"No PS&D balance sheet for {commodity} / {region} / {yr}")
        return {"commodity": commodity, "region": region, "market_year": yr,
                "line_items": [dict(r) for r in rows]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
