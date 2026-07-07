"""
FAO (Food and Agriculture Organization) Client
Provides UN global food price indices and commodity data from the local foodberg.db

Data loaded by rebake_history.py from FAOSTAT API and FAO bulk data files.
All queries read from the global_prices table (source='FAO', 'FAOSTAT', 'FAOSTAT CPI').

Previously contained hardcoded mock data generators — replaced with real DB queries
per the 2026-07-04 data-discovery audit quick fix.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class FAOClient:
    """Reads FAO food-price and CPI data from the local foodberg.db."""

    # FAO source labels in global_prices.source
    FAO_SOURCES = ("FAO", "FAOSTAT", "FAOSTAT CPI")

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / "data" / "foodberg.db")
        self.db_path = db_path
        _check = Path(self.db_path)
        if not _check.exists():
            logger.warning("foodberg.db not found at %s; queries will return empty results.", self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_food_price_index(self, category: str = "overall") -> Dict:
        """Return the latest month's value for a FAO food-price category.

        Maps *category* to the commodity string stored in global_prices.
        Returns an empty dict when no data is available (caller must not
        fabricate values).
        """
        label = self.categories.get(category)
        if label is None:
            return {"error": f"unknown category: {category}"}

        conn = self._connect()
        try:
            cur = conn.execute(
                """SELECT date, price
                   FROM global_prices
                   WHERE commodity = ?
                     AND source IN ({})
                   ORDER BY date DESC
                   LIMIT 1""".format(",".join("?" for _ in self.FAO_SOURCES)),
                (label, *self.FAO_SOURCES),
            )
            row = cur.fetchone()
            if row is None:
                return {"category": category, "error": "no data in global_prices"}

            return {
                "category": category,
                "index_name": label,
                "current_index": row["price"],
                "date": row["date"],
                "base_note": "source data from global_prices; base period varies",
            }
        finally:
            conn.close()

    def get_historical_series(
        self, category: str = "overall", limit: int = 300
    ) -> List[Dict]:
        """Return monthly historical observations for a category."""
        label = self.categories.get(category)
        if label is None:
            return []

        conn = self._connect()
        try:
            cur = conn.execute(
                """SELECT date, price
                   FROM global_prices
                   WHERE commodity = ?
                     AND source IN ({})
                   ORDER BY date ASC
                   LIMIT ?""".format(",".join("?" for _ in self.FAO_SOURCES)),
                (label, *self.FAO_SOURCES, limit),
            )
            return [
                {
                    "date": row["date"],
                    "index": round(row["price"], 1),
                    "category": category,
                }
                for row in cur.fetchall()
                if row["price"] is not None
            ]
        finally:
            conn.close()

    def get_all_indices(self) -> Dict:
        """Return current values and trends for all FAO categories."""
        indices = {}
        conn = self._connect()
        try:
            for cat_key, cat_label in self.categories.items():
                cur = conn.execute(
                    """SELECT date, price
                       FROM global_prices
                       WHERE commodity = ?
                         AND source IN ({})
                       ORDER BY date DESC
                       LIMIT 1""".format(",".join("?" for _ in self.FAO_SOURCES)),
                    (cat_label, *self.FAO_SOURCES),
                )
                row = cur.fetchone()
                if row:
                    indices[cat_key] = {
                        "current_index": row["price"],
                        "date": row["date"],
                        "label": cat_label,
                    }
                else:
                    indices[cat_key] = {"error": "no data"}

            # Previous-month comparison for overall trend
            overall_label = self.categories.get("overall")
            if overall_label:
                cur = conn.execute(
                    """SELECT date, price
                       FROM global_prices
                       WHERE commodity = ?
                         AND source IN ({})
                       ORDER BY date DESC
                       LIMIT 2""".format(",".join("?" for _ in self.FAO_SOURCES)),
                    (overall_label, *self.FAO_SOURCES),
                )
                rows = cur.fetchall()
                if len(rows) >= 2:
                    latest = rows[0]["price"]
                    prev = rows[1]["price"]
                    pct_change = round((latest - prev) / prev * 100, 1) if prev else 0
                else:
                    pct_change = 0
            else:
                pct_change = 0

        finally:
            conn.close()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "FAO - Food and Agriculture Organization (via foodberg.db)",
            "indices": indices,
            "summary": {
                "overall_index": indices.get("overall", {}).get("current_index"),
                "trend": self._trend_label(pct_change),
                "change_pct": pct_change,
            },
        }

    def get_fao_producer_prices(
        self,
        commodity: Optional[str] = None,
        country: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict]:
        """Query FAOSTAT producer prices (167K rows loaded by rebake_history)."""
        conn = self._connect()
        try:
            query = "SELECT * FROM global_prices WHERE source = 'FAOSTAT'"
            params = []

            if commodity:
                query += " AND commodity LIKE ?"
                params.append(f"%{commodity}%")
            if country:
                query += " AND country LIKE ?"
                params.append(f"%{country}%")
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date DESC LIMIT ?"
            params.append(limit)

            cur = conn.execute(query, params)
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_fao_cpi(
        self,
        country: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict]:
        """Query FAOSTAT CPI data (63K rows loaded by rebake_history)."""
        conn = self._connect()
        try:
            query = "SELECT * FROM global_prices WHERE source = 'FAOSTAT CPI'"
            params = []

            if country:
                query += " AND country LIKE ?"
                params.append(f"%{country}%")
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date DESC LIMIT ?"
            params.append(limit)

            cur = conn.execute(query, params)
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def categories(self) -> Dict[str, str]:
        return {
            "meat": "FAO Food Price Index - Meat",
            "dairy": "FAO Food Price Index - Dairy",
            "cereals": "FAO Food Price Index - Cereals",
            "oils": "FAO Food Price Index - Oils",
            "sugar": "FAO Food Price Index - Sugar",
            "overall": "FAO Food Price Index - Overall",
        }

    @staticmethod
    def _trend_label(pct_change: float) -> str:
        if pct_change > 2:
            return "strongly_increasing"
        if pct_change > 0.5:
            return "increasing"
        if pct_change < -2:
            return "strongly_decreasing"
        if pct_change < -0.5:
            return "decreasing"
        return "stable"

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_to_excel(self, filepath: str):
        """Export FAO price-index data to Druck-compliant Excel (one sheet)."""
        conn = self._connect()
        try:
            cur = conn.execute(
                """SELECT commodity, date, price, unit, country, region, source
                   FROM global_prices
                   WHERE source IN ({})
                   ORDER BY commodity, date ASC""".format(
                    ",".join("?" for _ in self.FAO_SOURCES)
                ),
                self.FAO_SOURCES,
            )
            rows = [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

        if not rows:
            return filepath  # nothing to export

        df = pd.DataFrame(rows)
        df.to_excel(filepath, sheet_name="FAO_Prices", index=False)
        return filepath


# ------------------------------------------------------------------
# Example usage
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("FAO Client — real DB queries (no mock data)")
    client = FAOClient()

    indices = client.get_all_indices()
    summary = indices.get("summary", {})
    print(f"\n  Overall index: {summary.get('overall_index')}")
    print(f"  Trend:         {summary.get('trend')}")
    print(f"  MoM change:    {summary.get('change_pct')}%")

    # Sample historical data
    history = client.get_historical_series("overall", limit=5)
    print("\n  Last 5 historical data points:")
    for pt in history[-5:]:
        print(f"    {pt['date']}: {pt['index']}")

    # Producer prices sample
    pp = client.get_fao_producer_prices(limit=3)
    print(f"\n  Producer prices sample ({len(pp)} of 167K+):")
    for row in pp:
        print(f"    {row['commodity']} | {row['country']} | {row['date']} | {row['price']}")

    # CPI sample
    cpi = client.get_fao_cpi(limit=3)
    print(f"\n  CPI sample ({len(cpi)} of 63K+):")
    for row in cpi:
        print(f"    {row['commodity']} | {row['country']} | {row['date']} | {row['price']}")