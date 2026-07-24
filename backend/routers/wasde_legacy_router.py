"""
wasde_legacy_router.py — WASDE Legacy (historical machine-extracted) endpoints.

Self-contained APIRouter deployed additively; wire in main.py with:
    from routers.wasde_legacy_router import router as legacy_router
    app.include_router(legacy_router)

Reads the `wasde_legacy` table (114,741 rows, 1979–2009, machine-extracted from
historical WASDE PDFs by Hopper Line v2 + T12 ASCII parsers). HONESTY RULES:
- Only serves rows with non-NULL commodity AND region (attributed rows).
- NEVER serves 1970s rows (2.2% clean rate — research-internal only).
- Labels coverage honestly: per-decade/per-commodity matrix.
- Units as printed per row; no silent conversion.
- No interpolation across gaps.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/legacy", tags=["wasde-legacy"])

_DB = Path(__file__).resolve().parent.parent / "data" / "foodberg.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB))
    conn.row_factory = sqlite3.Row
    return conn


# ── Honesty guards ──────────────────────────────────────────────────────────
# Only rows with commodity AND region populated, market_year 1980/81 or later.
_ATTRIBUTED_WHERE = """
    commodity IS NOT NULL AND commodity != ''
    AND region IS NOT NULL AND region != ''
    AND CAST(SUBSTR(market_year, 1, 4) AS INTEGER) >= 1980
"""


@router.get("/commodities")
def legacy_commodities():
    """Commodities with attributed rows, year ranges, and row counts."""
    try:
        conn = _conn()
        rows = conn.execute(f"""
            SELECT commodity,
                   COUNT(*) AS row_count,
                   COUNT(DISTINCT attribute) AS n_attributes,
                   MIN(market_year) AS min_year,
                   MAX(market_year) AS max_year
            FROM wasde_legacy
            WHERE {_ATTRIBUTED_WHERE}
            GROUP BY commodity
            HAVING COUNT(*) >= 10
            ORDER BY row_count DESC
        """).fetchall()
        conn.close()
        return {
            "source": "WASDE legacy — machine-extracted from historical reports (1979–2009)",
            "source_note": (
                "Machine-extracted from historical USDA WASDE PDFs by Hopper Line v2 "
                "and T12 ASCII parsers. Partial coverage, 75.4% commodity-attributed "
                "overall. 1970s rows excluded (2.2% clean rate). See provenance for details."
            ),
            "attribution_rate": "75.4%",
            "count": len(rows),
            "commodities": [dict(r) for r in rows],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coverage")
def legacy_coverage():
    """Per-decade per-commodity coverage matrix — powers the honesty label."""
    try:
        conn = _conn()
        # Per-commodity x decade coverage
        rows = conn.execute(f"""
            SELECT commodity,
                   CASE
                     WHEN CAST(SUBSTR(market_year, 1, 4) AS INTEGER) BETWEEN 1980 AND 1989 THEN '1980s'
                     WHEN CAST(SUBSTR(market_year, 1, 4) AS INTEGER) BETWEEN 1990 AND 1999 THEN '1990s'
                     WHEN CAST(SUBSTR(market_year, 1, 4) AS INTEGER) >= 2000 THEN '2000s'
                     ELSE 'other'
                   END AS decade,
                   COUNT(*) AS attributed_rows,
                   MIN(market_year) AS min_my,
                   MAX(market_year) AS max_my,
                   COUNT(DISTINCT attribute) AS n_attributes,
                   COUNT(DISTINCT region) AS n_regions
            FROM wasde_legacy
            WHERE {_ATTRIBUTED_WHERE}
              AND commodity IN (
                SELECT commodity FROM wasde_legacy
                WHERE {_ATTRIBUTED_WHERE}
                GROUP BY commodity HAVING COUNT(*) >= 10
              )
            GROUP BY commodity, decade
            ORDER BY commodity, decade
        """).fetchall()

        # Overall per-decade totals — hardcoded ranges to avoid alias-in-subquery error
        totals = []
        for decade_label, y_start, y_end in [("1980s", 1980, 1989), ("1990s", 1990, 1999), ("2000s", 2000, 2009)]:
            row = conn.execute(f"""
                SELECT ? AS decade,
                       COUNT(*) AS attributed,
                       (SELECT COUNT(*) FROM wasde_legacy
                        WHERE CAST(SUBSTR(market_year, 1, 4) AS INTEGER) BETWEEN ? AND ?
                       ) AS total_rows
                FROM wasde_legacy
                WHERE {_ATTRIBUTED_WHERE}
                  AND CAST(SUBSTR(market_year, 1, 4) AS INTEGER) BETWEEN ? AND ?
            """, (decade_label, y_start, y_end, y_start, y_end)).fetchone()
            totals.append({
                "decade": row["decade"],
                "attributed": row["attributed"],
                "total_rows": row["total_rows"],
                "clean_pct": round(row["attributed"] * 100.0 / row["total_rows"], 1) if row["total_rows"] else 0,
            })

        conn.close()

        coverage_matrix = {}
        for r in rows:
            cov = dict(r)
            c = cov.pop("commodity")
            d = cov.pop("decade")
            coverage_matrix.setdefault(c, {})[d] = cov

        return {
            "source": "WASDE legacy coverage audit",
            "disclaimer": (
                "Machine-extracted from historical reports, 1979–2009, "
                "partial coverage — see provenance. 1970s excluded (2.2% clean). "
                "Gaps indicate decades where extraction could not reliably attribute "
                "commodity or region to parsed values."
            ),
            "per_decade_totals": totals,
            "coverage_matrix": coverage_matrix,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{commodity}/series")
def legacy_series(
    commodity: str,
    region: str = Query("World"),
    attribute: str | None = Query(None),
):
    """
    Attributed rows for a commodity, ordered by market_year.
    Returns {market_year, value, unit, attribute, region, attribution_label}.

    Only serves attributed rows (commodity + region populated, >= 1980).
    Units as printed — no silent conversion.
    """
    try:
        conn = _conn()
        where = f"""
            commodity = ? AND {_ATTRIBUTED_WHERE}
            AND region = ?
        """
        params: list = [commodity, region]

        if attribute:
            where += " AND attribute = ?"
            params.append(attribute)

        rows = conn.execute(f"""
            SELECT market_year, value, unit, attribute, region, attribution_label
            FROM wasde_legacy
            WHERE {where}
            ORDER BY market_year, attribute
        """, params).fetchall()

        attr_list = conn.execute(f"""
            SELECT DISTINCT attribute
            FROM wasde_legacy
            WHERE {where}
            ORDER BY attribute
        """, params).fetchall()

        conn.close()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No legacy data for {commodity} / {region}"
                + (f" / {attribute}" if attribute else ""),
            )

        return {
            "commodity": commodity,
            "region": region,
            "attribute_filter": attribute,
            "available_attributes": [r["attribute"] for r in attr_list],
            "n_rows": len(rows),
            "year_range": {
                "start": rows[0]["market_year"],
                "end": rows[-1]["market_year"],
            },
            "disclaimer": (
                "Machine-extracted from historical WASDE reports (1979–2009), "
                "partial coverage. Units as printed per row — no conversion. "
                "See /api/legacy/coverage for per-decade attribution rates."
            ),
            "data": [dict(r) for r in rows],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))