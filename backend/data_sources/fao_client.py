"""
FAO Food Price Index Client (OFFLINE / local-DB backed)

Serves the real FAO Food Price Index from the baked-in Foodberg SQLite database
(`global_prices` table, source='FAO') — NO outbound HTTP, NO API key.

Provenance: global_prices holds 431 real monthly FAO Food Price Index
observations per category (1990-2025, base 2014-2016 = 100):
    overall  -> indicator_code 'fao_food_overall'
    meat     -> 'fao_food_meat'
    dairy    -> 'fao_food_dairy'
    cereals  -> 'fao_food_cereals'
    oils     -> 'fao_food_oils'
    sugar    -> 'fao_food_sugar'

Per the Anu Framework "No Synthetic/Placeholder Data" rule, the previous
hardcoded mock numbers and generate_mock_historical() have been DELETED. A
category with no real local data returns {"status": "data_unavailable", ...}.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "data" / "foodberg.db")


class FAOClient:
    """Local-DB-backed FAO Food Price Index provider (offline)."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH

        # user category -> (display name, indicator_code in local DB)
        self.categories = {
            "meat": ("Meat Price Index", "fao_food_meat"),
            "dairy": ("Dairy Price Index", "fao_food_dairy"),
            "cereals": ("Cereal Price Index", "fao_food_cereals"),
            "oils": ("Oils Price Index", "fao_food_oils"),
            "sugar": ("Sugar Price Index", "fao_food_sugar"),
            "overall": ("FAO Food Price Index", "fao_food_overall"),
        }

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _fetch_series(self, indicator_code: str, limit: int = 36) -> List[Dict]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT price, unit, date FROM global_prices
                WHERE source = 'FAO' AND indicator_code = ?
                ORDER BY date DESC LIMIT ?
                """,
                (indicator_code, limit),
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    async def get_food_price_index(self, category: str = "overall") -> Dict:
        """Get FAO Food Price Index data for a category from the local DB."""
        meta = self.categories.get(category.lower())
        if not meta:
            return {
                "status": "data_unavailable",
                "category": category,
                "reason": (
                    "Unknown category. Available: "
                    + ", ".join(sorted(self.categories.keys()))
                ),
            }
        name, indicator_code = meta
        rows = self._fetch_series(indicator_code, limit=36)
        if not rows:
            return {
                "status": "data_unavailable",
                "category": category,
                "index_name": name,
                "reason": f"No local FAO rows for {indicator_code}.",
            }

        current = rows[0]["price"]
        prev = rows[1]["price"] if len(rows) > 1 else None
        year_ago = rows[12]["price"] if len(rows) > 12 else None

        change_pct = (
            round(((current - prev) / prev) * 100, 1)
            if prev not in (None, 0)
            else None
        )
        yoy_pct = (
            round(((current - year_ago) / year_ago) * 100, 1)
            if year_ago not in (None, 0)
            else None
        )

        historical = [
            {
                "date": str(r["date"])[:7],
                "index": r["price"],
                "category": category,
            }
            for r in reversed(rows[:24])
        ]

        return {
            "category": category,
            "index_name": name,
            "current_index": current,
            "previous_month": prev,
            "change_percent": change_pct,
            "date": str(rows[0]["date"])[:7],
            "year_ago_index": year_ago,
            "yoy_change_percent": yoy_pct,
            "base_period": rows[0]["unit"] or "2014-2016=100",
            "source": "FAO (local database, offline)",
            "historical_data": historical,
        }

    async def get_all_indices(self) -> Dict:
        """Get all FAO food price indices from the local DB."""
        indices = {}
        for category in self.categories.keys():
            indices[category] = await self.get_food_price_index(category)

        overall = indices.get("overall", {})
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "FAO - Food and Agriculture Organization (local database, offline)",
            "indices": indices,
            "summary": {
                "overall_index": overall.get("current_index"),
                "trend": self.calculate_trend(indices),
                "alert": self.generate_alert(indices),
            },
        }

    def calculate_trend(self, indices: Dict) -> str:
        overall = indices.get("overall", {})
        change = overall.get("change_percent")
        if change is None:
            return "unknown"
        if change > 2:
            return "strongly_increasing"
        elif change > 0.5:
            return "increasing"
        elif change < -2:
            return "strongly_decreasing"
        elif change < -0.5:
            return "decreasing"
        return "stable"

    def generate_alert(self, indices: Dict) -> Optional[str]:
        overall = indices.get("overall", {})
        change = overall.get("change_percent")
        if change is not None and abs(change) > 3:
            direction = "spike" if change > 0 else "drop"
            return f"FAO Food Price Index {direction}: {abs(change):.1f}% in last month"
        return None
