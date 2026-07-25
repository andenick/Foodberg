"""
Economic Indicators Client (OFFLINE / local-DB backed)

Serves FRED/BLS economic indicators from the baked-in Foodberg SQLite database
(`economic_indicators` table) — NO outbound HTTP, NO FRED_API_KEY required.

Provenance: economic_indicators holds 14,640 real FRED/BLS observations
(2000-2026), including the series this client reports:
  - CPIUFDSL  -> Food CPI
  - WPU02     -> PPI Processed Foods
  - FEDFUNDS / CPIAUCSL etc. for headline context.

Per the Anu Framework "No Synthetic/Placeholder Data" rule, if a required series
is absent from the local DB the indicator is reported as data_unavailable rather
than fabricated.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "data" / "foodberg.db")


class FREDClient:
    """Local-DB-backed economic indicator provider (offline).

    Class/method names retained for route compatibility; no FRED API call is
    ever made. All data comes from the local `economic_indicators` table.
    """

    def __init__(self, api_key: Optional[str] = None, db_path: Optional[str] = None):
        # api_key kept for signature compatibility; intentionally unused offline.
        self.db_path = db_path or DEFAULT_DB_PATH
        self.series = {
            "food_cpi": "CPIUFDSL",
            "ppi_food": "WPU02",
            "inflation": "CPIAUCSL",
        }

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def get_series_data(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Fetch observations for a series from the local DB (newest first)."""
        conn = self._connect()
        try:
            cur = conn.cursor()
            # Restrict to canonical month-start observations (date '...-01').
            # The DB mixes vintages for some series (e.g. CPIAUCSL has both the
            # clean first-of-month monthly index AND intra-month dated rows from
            # a different vintage); filtering to day-01 yields the real, evenly
            # monthly-spaced series so YoY math is correct (no fabrication).
            params = [series_id]
            sql = (
                "SELECT date, value, series_id FROM economic_indicators "
                "WHERE series_id = ? AND substr(date, 9, 2) = '01'"
            )
            if start_date:
                sql += " AND date >= ?"
                params.append(start_date)
            sql += " ORDER BY date DESC LIMIT ?"
            params.append(limit)
            cur.execute(sql, params)
            rows = cur.fetchall()
        finally:
            conn.close()

        # Deduplicate by date (the DB has overlapping category labels for the
        # same series_id/date); keep the first (newest-ordered) per date.
        seen = set()
        out = []
        for r in rows:
            d = str(r["date"])[:10]
            if d in seen:
                continue
            seen.add(d)
            out.append(
                {"date": d, "value": r["value"], "series_id": r["series_id"]}
            )
        return out

    def _yoy(self, data: List[Dict]) -> float:
        if len(data) >= 13 and data[0]["value"] and data[12]["value"]:
            latest = data[0]["value"]
            year_ago = data[12]["value"]
            return round(((latest - year_ago) / year_ago) * 100, 2)
        return 0.0

    async def get_food_cpi(self, months: int = 24) -> Dict:
        data = await self.get_series_data(self.series["food_cpi"], limit=months)
        if not data:
            return {
                "indicator": "Food CPI",
                "status": "data_unavailable",
                "reason": "Series CPIUFDSL not present in local database.",
            }
        yoy = self._yoy(data)
        return {
            "indicator": "Food CPI",
            "current_value": data[0]["value"],
            "date": data[0]["date"],
            "yoy_change_percent": yoy,
            "trend": "increasing" if yoy > 0 else "decreasing",
            "data": data[:12],
        }

    async def get_ppi_food(self, months: int = 24) -> Dict:
        data = await self.get_series_data(self.series["ppi_food"], limit=months)
        if not data:
            return {
                "indicator": "Food PPI",
                "status": "data_unavailable",
                "reason": "Series WPU02 not present in local database.",
            }
        yoy = self._yoy(data)
        return {
            "indicator": "Food PPI",
            "current_value": data[0]["value"],
            "date": data[0]["date"],
            "yoy_change_percent": yoy,
            "trend": "increasing" if yoy > 0 else "decreasing",
            "data": data[:12],
        }

    async def get_inflation_rate(self) -> Dict:
        # Headline CPI (CPIAUCSL) — report level + YoY as the inflation gauge.
        data = await self.get_series_data(self.series["inflation"], limit=24)
        if not data:
            return {
                "indicator": "Inflation Rate (CPI All Items)",
                "status": "data_unavailable",
                "reason": "Series CPIAUCSL not present in local database.",
            }
        yoy = self._yoy(data)
        return {
            "indicator": "Inflation Rate (CPI All Items YoY)",
            "current_value": yoy,
            "cpi_level": data[0]["value"],
            "date": data[0]["date"],
            "data": data[:12],
        }

    async def get_all_indicators(self) -> Dict:
        """All food-relevant economic indicators, from the local DB."""
        food_cpi = await self.get_food_cpi()
        ppi_food = await self.get_ppi_food()
        inflation = await self.get_inflation_rate()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "FRED/BLS (local database, offline)",
            "indicators": {
                "cpi_food": food_cpi,
                "ppi_food": ppi_food,
                "inflation": inflation,
            },
            "summary": {
                "food_inflation": food_cpi.get("yoy_change_percent"),
                "producer_pressure": ppi_food.get("yoy_change_percent"),
                "overall_inflation": inflation.get("current_value"),
                "outlook": self.generate_outlook(food_cpi, ppi_food, inflation),
            },
        }

    def generate_outlook(self, cpi, ppi, inflation) -> str:
        """Simple outlook based on indicators (graceful if any unavailable)."""
        cpi_yoy = cpi.get("yoy_change_percent")
        ppi_yoy = ppi.get("yoy_change_percent")
        if cpi_yoy is None or ppi_yoy is None:
            return "Insufficient local data to compute outlook"
        if ppi_yoy > cpi_yoy:
            return "Producer prices rising faster than consumer - expect price increases"
        elif cpi_yoy > 5:
            return "High food inflation - cost pressures significant"
        elif cpi_yoy < 2:
            return "Stable food prices - good environment for menu planning"
        return "Moderate inflation - monitor closely"
