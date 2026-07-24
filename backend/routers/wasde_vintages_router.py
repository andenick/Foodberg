"""
wasde_vintages_router.py — WASDE Vintage / Revision Trajectory endpoints.

Self-contained APIRouter so it can be deployed additively to the box without
overwriting main.py. Wire in main.py with:

    from routers.wasde_vintages_router import router as vintages_router
    app.include_router(vintages_router)

Reads the `wasde_vintages` table (952k+ rows, 193 reports 2010-04→2026-07)
from the same SQLite file the rest of the backend uses.

Each row records what one WASDE report said about one commodity x attribute x
region x market_year on one publication date — the "as-reported" trajectory.
Units may change across eras (e.g. Million Bushels → Million Metric Tons);
every row carries its own unit. No silent conversion.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/vintages", tags=["wasde-vintages"])

_DB = Path(__file__).resolve().parent.parent / "data" / "foodberg.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB))
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/commodities")
def vintages_commodities():
    """Distinct commodities with report counts and market_year range."""
    try:
        conn = _conn()
        rows = conn.execute(
            """
            SELECT commodity,
                   COUNT(*) AS report_count,
                   COUNT(DISTINCT report_date) AS n_reports,
                   MIN(report_date) AS first_report,
                   MAX(report_date) AS last_report,
                   MIN(NULLIF(market_year, '')) AS min_market_year,
                   MAX(market_year) AS max_market_year
            FROM wasde_vintages
            GROUP BY commodity
            ORDER BY commodity
            """
        ).fetchall()
        conn.close()
        return {
            "source": "USDA WASDE vintages (as-reported trajectory per report date)",
            "count": len(rows),
            "commodities": [dict(r) for r in rows],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{commodity}/attributes")
def vintages_attributes(commodity: str):
    """Attributes and regions available for a commodity."""
    try:
        conn = _conn()
        attrs = conn.execute(
            """
            SELECT DISTINCT attribute
            FROM wasde_vintages
            WHERE commodity = ?
            ORDER BY attribute
            """,
            (commodity,),
        ).fetchall()
        regions = conn.execute(
            """
            SELECT DISTINCT region
            FROM wasde_vintages
            WHERE commodity = ? AND region != ''
            ORDER BY region
            """,
            (commodity,),
        ).fetchall()
        conn.close()
        if not attrs:
            raise HTTPException(status_code=404, detail=f"No vintage data for {commodity}")
        return {
            "commodity": commodity,
            "attributes": [r["attribute"] for r in attrs],
            "regions": [r["region"] for r in regions],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{commodity}/series")
def vintages_series(
    commodity: str,
    attribute: str = Query(...),
    region: str = Query("World"),
    market_year: str = Query(...),
):
    """
    The as-reported trajectory: rows ordered by report_date, each carrying
    {report_date, wasde_number, value, unit, release_date}.
    Units per row — the client decides what to display; no silent conversion.
    """
    try:
        conn = _conn()
        rows = conn.execute(
            """
            SELECT report_date, release_date, wasde_number, value, unit,
                   proj_est_flag
            FROM wasde_vintages
            WHERE commodity = ? AND attribute = ? AND region = ? AND market_year = ?
            ORDER BY release_date
            """,
            (commodity, attribute, region, market_year),
        ).fetchall()
        conn.close()
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No vintage series for {commodity} / {region} / {attribute} / {market_year}",
            )
        units_used = list(dict.fromkeys(r["unit"] for r in rows).keys())
        return {
            "commodity": commodity,
            "region": region,
            "attribute": attribute,
            "market_year": market_year,
            "n_reports": len(rows),
            "units_used": units_used,
            "note": (
                "Units may change across the reporting history. "
                "Each row carries its own unit — filter on the client side "
                "before comparing values."
                if len(units_used) > 1 else None
            ),
            "data": [
                {
                    "report_date": r["report_date"],
                    "release_date": r["release_date"],
                    "wasde_number": r["wasde_number"],
                    "value": r["value"],
                    "unit": r["unit"],
                    "proj_est_flag": r["proj_est_flag"] or None,
                }
                for r in rows
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{commodity}/market-years")
def vintages_market_years(commodity: str):
    """Market years with coverage for a commodity."""
    try:
        conn = _conn()
        rows = conn.execute(
            """
            SELECT market_year,
                   COUNT(*) AS report_count,
                   MIN(release_date) AS first_report,
                   MAX(release_date) AS last_report,
                   COUNT(DISTINCT attribute) AS n_attributes
            FROM wasde_vintages
            WHERE commodity = ? AND market_year != ''
            GROUP BY market_year
            ORDER BY market_year DESC
            """,
            (commodity,),
        ).fetchall()
        conn.close()
        if not rows:
            raise HTTPException(status_code=404, detail=f"No vintage data for {commodity}")
        return {
            "commodity": commodity,
            "market_years": [dict(r) for r in rows],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))