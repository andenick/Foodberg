"""
Global Commodity Price Client (OFFLINE / local-DB backed)

Serves per-commodity international price series from the baked-in Foodberg
SQLite database (`global_prices` table) — NO outbound HTTP, NO API key.

Provenance: the only real per-commodity monthly USD price series present in the
local DB are Alpha Vantage continuous-contract series (WHEAT, CORN, COFFEE,
SUGAR, COTTON), 1992-2026, stored in `global_prices` with source='Alpha Vantage'.
The World Bank "Pink Sheet" per-commodity USD prices (PWHEAMT, PBEEF, ...) were
NEVER ingested into this DB — the only World-Bank rows present are development
indicators (cereal production, ag value-added, etc.), not commodity prices.

Per the Anu Framework "No Synthetic/Placeholder Data" rule, a commodity that has
no real local price series returns {"status": "data_unavailable", ...}. No mock,
hardcoded, or fabricated numbers are ever returned.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, List, Dict, Optional

# Default location of the baked-in SQLite DB (backend/data/foodberg.db).
DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "data" / "foodberg.db")


class WorldBankClient:
    """Local-DB-backed commodity price provider (offline).

    The class name is retained for route compatibility, but it no longer makes
    any World Bank API call. All data comes from the local `global_prices` table.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH

        # Map user-facing commodity name -> (source, indicator_code) actually
        # present in the local DB. Only real, provenance-traceable series here.
        # These are the Alpha Vantage continuous-contract monthly USD series.
        self.commodities = {
            "wheat": ("Alpha Vantage", "WHEAT"),
            "corn": ("Alpha Vantage", "CORN"),
            "maize": ("Alpha Vantage", "CORN"),  # maize == corn
            "coffee": ("Alpha Vantage", "COFFEE"),
            "sugar": ("Alpha Vantage", "SUGAR"),
            "cotton": ("Alpha Vantage", "COTTON"),
        }

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def get_commodity_price(
        self,
        commodity: str,
        start_year: int = 2020,
    ) -> Dict:
        """Return commodity price series from the local DB.

        Returns a {"status": "data_unavailable", ...} payload (never mock data)
        when the requested commodity has no real local price series.
        """
        key = commodity.lower().strip()
        mapping = self.commodities.get(key)

        if not mapping:
            return {
                "status": "data_unavailable",
                "commodity": commodity,
                "reason": (
                    "No real local commodity price series for this commodity. "
                    "Offline build only ships Alpha Vantage monthly USD series for: "
                    + ", ".join(sorted(self.commodities.keys()))
                    + ". (World Bank Pink Sheet per-commodity prices were not "
                    "ingested into the local database.)"
                ),
                "source": "local database (global_prices)",
            }

        source, indicator_code = mapping
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT price, unit, currency, region, date
                FROM global_prices
                WHERE source = ? AND indicator_code = ?
                ORDER BY date DESC
                LIMIT 240
                """,
                (source, indicator_code),
            )
            rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            return {
                "status": "data_unavailable",
                "commodity": commodity,
                "reason": (
                    f"Local database has no rows for {indicator_code} "
                    f"(source={source})."
                ),
                "source": "local database (global_prices)",
            }

        processed = [
            {
                "date": str(r["date"])[:10],
                "value": r["price"],
                "commodity": commodity,
            }
            for r in rows
            if r["price"] is not None
        ]
        values = [p["value"] for p in processed]
        unit = rows[0]["unit"] or "USD per unit"

        return {
            "commodity": commodity,
            "unit": unit,
            "currency": rows[0]["currency"] or "USD",
            "current_price": values[0] if values else None,
            "average": sum(values) / len(values) if values else None,
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "data": processed[:24],  # most recent 24 months
            "source": f"{source} (local database, offline)",
            "indicator_code": indicator_code,
        }

    async def get_multiple_commodities(self, commodities: List[str]) -> Dict:
        """Get price data for multiple commodities from the local DB."""
        results = {}
        for commodity in commodities:
            results[commodity] = await self.get_commodity_price(commodity)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "Local database (global_prices) — offline, no outbound calls",
            "commodities": results,
        }

    # ------------------------------------------------------------------
    # Geographic comparison (the REAL multi-country data in the local DB):
    # World Bank development indicators, annual, per named region, 1990-2024.
    # These back the Geographic page — the per-commodity price series above
    # are GLOBAL-only and cannot be compared across countries.
    # ------------------------------------------------------------------

    def get_geo_indicators(self) -> List[Dict]:
        """List the World Bank indicators with per-region annual coverage."""
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT indicator_code,
                       commodity              AS name,
                       MIN(unit)              AS unit,
                       COUNT(DISTINCT region) AS n_regions,
                       MIN(CAST(strftime('%Y', date) AS INTEGER)) AS year_start,
                       MAX(CAST(strftime('%Y', date) AS INTEGER)) AS year_end,
                       COUNT(*)               AS n_obs
                FROM global_prices
                WHERE source = 'World Bank' AND region IS NOT NULL AND region != ''
                GROUP BY indicator_code
                ORDER BY n_obs DESC
                """
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_geo_series(self, indicator_code: str) -> Dict:
        """All (region, year, value) rows for one World Bank indicator.

        Region names are the clean human labels stored in `region`
        (United States, China, Brazil, India, Australia, Canada, Argentina,
        European Union, World). Annual observations; one value per
        region-year (averaged defensively if duplicates exist).
        """
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT region,
                       CAST(strftime('%Y', date) AS INTEGER) AS year,
                       AVG(price) AS value,
                       MIN(unit)  AS unit,
                       MIN(commodity) AS name
                FROM global_prices
                WHERE source = 'World Bank' AND indicator_code = ?
                  AND region IS NOT NULL AND region != '' AND price IS NOT NULL
                GROUP BY region, year
                ORDER BY region, year
                """,
                (indicator_code,),
            )
            rows = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

        if not rows:
            return {
                "status": "data_unavailable",
                "indicator_code": indicator_code,
                "reason": "No World Bank rows for this indicator in the local database.",
            }

        regions = sorted({r["region"] for r in rows})
        return {
            "indicator_code": indicator_code,
            "name": rows[0]["name"],
            "unit": rows[0]["unit"],
            "regions": regions,
            "n_obs": len(rows),
            "year_range": {
                "start": min(r["year"] for r in rows),
                "end": max(r["year"] for r in rows),
            },
            "data": [
                {"region": r["region"], "year": r["year"], "value": r["value"]}
                for r in rows
            ],
            "source": "World Bank (local database, offline)",
        }

    # Hand-curated links from Foodberg's NASS commodity slugs to the matching
    # series in OTHER sources. Only real, verified name matches — a commodity
    # with no link in a source honestly has no series there.
    COMMODITY_LINKS: Dict[str, Dict[str, str]] = {
        "wheat":    {"pinksheet": "Wheat, US HRW"},
        "corn":     {"pinksheet": "Maize"},
        "rice":     {"pinksheet": "Rice, Thai 5% ", "retail": "Rice, white, long grain, uncooked"},
        "barley":   {"pinksheet": "Barley"},
        "sorghum":  {"pinksheet": "Sorghum"},
        "soybeans": {"pinksheet": "Soybeans"},
        "cotton":   {"pinksheet": "Cotton, A Index"},
        "sugarcane": {"pinksheet": "Sugar, world"},
        "cattle":   {"pinksheet": "Beef", "retail": "Ground beef, 100% beef"},
        "chickens": {"pinksheet": "Chicken", "retail": "Chicken, fresh, whole"},
        "hogs":     {"retail": "Pork chops, boneless"},
        "eggs":     {"retail": "Eggs, grade A, large"},
        "milk":     {"retail": "Milk, fresh, whole, fortified"},
        "potatoes": {"retail": "Potatoes, white"},
        "oranges":  {"pinksheet": "Orange", "retail": "Oranges, navel"},
        # 'apples' -> 'Apples, red delicious' is a REAL series, but BLS stopped
        # publishing it in 2017-10. It is retained (real history is worth
        # showing) and is now automatically flagged `discontinued` by
        # _liveness() so it can never again be presented as current. P0-6.
        "apples":   {"retail": "Apples, red delicious"},
        # 'strawberries' -> 'Strawberries, dry pint' REMOVED 2026-07-24 (P0-6):
        # that item name resolves to ZERO rows in retail_prices. It was a dead
        # mapping failing silently — the UI offered a BLS retail tab that could
        # never render. BLS AP carries no live strawberry item, so the honest
        # state is "no retail series", not a broken link.
        "peanuts":  {"pinksheet": "Groundnuts"},
        "coffee":   {"pinksheet": "Coffee, Arabica", "retail": "Coffee, 100% ground roast, all sizes"},
        "sugar":    {"pinksheet": "Sugar, world", "retail": "Sugar, white, all sizes"},
    }

    def _pinksheet_name(self, slug: str) -> Optional[str]:
        return self.COMMODITY_LINKS.get(slug, {}).get("pinksheet")

    def _retail_name(self, slug: str) -> Optional[str]:
        return self.COMMODITY_LINKS.get(slug, {}).get("retail")

    # -- Liveness (P0-6 / S5) ------------------------------------------------
    # Classify a series by its LAST REAL OBSERVATION, never by item-list
    # membership or a declared end_year. Fifteen BLS AP items carry a 2025-M10
    # placeholder (footnoted "data unavailable due to the 2025 lapse in
    # appropriations") whose real data is years older; several more went dark
    # in 2017-2020 with no announcement. Both classes must be visibly stale.
    #
    # Self-calibrating: a series is judged against the newest observation in
    # its OWN source catalog, so it does not need a hardcoded "today".

    LIVENESS_STALE_MONTHS = 6
    LIVENESS_DISCONTINUED_MONTHS = 24

    @staticmethod
    def _parse_ym(value: str):
        """
        Parse 'YYYY-MM-DD', 'YYYY-MM' or a bare 'YYYY' into (year, month).

        Bare years (the NASS catalog reports annual coverage as a year) are
        treated as December, so an annual series is only judged stale once the
        whole year is behind.
        """
        try:
            s = str(value).strip()
            year = int(s[:4])
        except (ValueError, TypeError):
            return None
        if len(s) >= 7 and s[4] == "-":
            try:
                return year, int(s[5:7])
            except ValueError:
                return None
        return year, 12

    @classmethod
    def _months_between(cls, earlier: str, later: str) -> Optional[int]:
        """Whole months between two dates (see _parse_ym for accepted forms)."""
        a, b = cls._parse_ym(earlier), cls._parse_ym(later)
        if a is None or b is None:
            return None
        return (b[0] - a[0]) * 12 + (b[1] - a[1])

    @classmethod
    def _liveness(cls, series_end: Optional[str],
                  catalog_end: Optional[str]) -> Dict[str, Any]:
        """
        Return {'status', 'months_behind', 'last_real_observation'} for a
        series, relative to the newest observation in its source catalog.

        status is one of: 'live' | 'stale' | 'discontinued' | 'unknown'
        """
        if not series_end or not catalog_end:
            return {"status": "unknown", "months_behind": None,
                    "last_real_observation": series_end}
        behind = cls._months_between(series_end, catalog_end)
        if behind is None:
            status = "unknown"
        elif behind >= cls.LIVENESS_DISCONTINUED_MONTHS:
            status = "discontinued"
        elif behind >= cls.LIVENESS_STALE_MONTHS:
            status = "stale"
        else:
            status = "live"
        return {"status": status, "months_behind": behind,
                "last_real_observation": series_end}

    def get_price_coverage(self) -> Dict:
        """Multi-source price-history coverage per commodity (honest UI labels).

        Sources surveyed (all baked, offline):
          av        Alpha Vantage monthly global spot (5 commodities)
          nass      USDA NASS PRICE RECEIVED, national (annual+monthly, to ~1908)
          pinksheet World Bank Pink Sheet monthly global (via curated link)
          retail    BLS Average Price monthly US retail (via curated link)
        """
        conn = self._connect()
        try:
            cur = conn.cursor()
            # Alpha Vantage monthly series
            av = {}
            cur.execute(
                "SELECT indicator_code, COUNT(*) n, MIN(date) s, MAX(date) e "
                "FROM global_prices WHERE source='Alpha Vantage' "
                "AND price IS NOT NULL GROUP BY indicator_code")
            for r in cur.fetchall():
                av[str(r["indicator_code"]).lower()] = {
                    "points": r["n"], "frequency": "monthly",
                    "start": str(r["s"])[:10], "end": str(r["e"])[:10],
                    "label": "Alpha Vantage global spot",
                }
            # NASS farm-gate prices (national)
            nass = {}
            cur.execute(
                "SELECT commodity, COUNT(DISTINCT year) ny, COUNT(*) n, "
                "MIN(year) y0, MAX(year) y1 FROM wasde_data "
                "WHERE statistic_category='PRICE RECEIVED' AND agg_level='NATIONAL' "
                "AND numeric_value IS NOT NULL GROUP BY commodity")
            for r in cur.fetchall():
                if r["ny"] and r["ny"] > 1:
                    nass[str(r["commodity"]).lower()] = {
                        "points": r["n"], "n_years": r["ny"],
                        "frequency": "annual+monthly",
                        "start": str(r["y0"]), "end": str(r["y1"]),
                        "label": "USDA NASS farm-gate price",
                    }
            # Pink Sheet series catalog
            pink = {}
            cur.execute(
                "SELECT commodity, unit, COUNT(*) n, MIN(date) s, MAX(date) e "
                "FROM global_prices WHERE source='World Bank Pink Sheet' "
                "GROUP BY commodity")
            for r in cur.fetchall():
                pink[r["commodity"]] = {
                    "points": r["n"], "unit": r["unit"], "frequency": "monthly",
                    "start": str(r["s"])[:10], "end": str(r["e"])[:10],
                }
            # BLS retail item catalog
            retail = {}
            cur.execute(
                "SELECT food_item, unit, COUNT(*) n, MIN(date) s, MAX(date) e "
                "FROM retail_prices WHERE source='BLS AP' GROUP BY food_item")
            for r in cur.fetchall():
                retail[r["food_item"]] = {
                    "points": r["n"], "unit": r["unit"], "frequency": "monthly",
                    "start": str(r["s"])[:10], "end": str(r["e"])[:10],
                }
            # FAOSTAT producer-price footprint (for the Geographic page)
            cur.execute(
                "SELECT COUNT(DISTINCT commodity) items, "
                "COUNT(DISTINCT country) countries, "
                "MIN(date) s, MAX(date) e FROM global_prices "
                "WHERE source='FAOSTAT'")
            fr = cur.fetchone()
            faostat = {
                "items": fr["items"], "countries": fr["countries"],
                "start": str(fr["s"])[:10] if fr["s"] else None,
                "end": str(fr["e"])[:10] if fr["e"] else None,
            }
        finally:
            conn.close()

        if "corn" in av:
            av["maize"] = av["corn"]

        # P0-6 / S5: stamp every catalog entry with a liveness verdict derived
        # from its LAST REAL OBSERVATION, measured against the newest
        # observation in its own source catalog.
        for catalog in (av, nass, pink, retail):
            catalog_end = max(
                (e["end"] for e in catalog.values() if e.get("end")),
                default=None)
            for entry in catalog.values():
                entry["liveness"] = self._liveness(entry.get("end"), catalog_end)

        # Assemble per-commodity source map over the NASS commodity universe
        # plus anything AV covers.
        commodities: Dict[str, Dict] = {}
        slugs = set(nass) | set(av) | set(self.COMMODITY_LINKS)
        for slug in sorted(slugs):
            entry: Dict[str, Dict] = {}
            if slug in av:
                entry["av"] = av[slug]
            if slug in nass:
                entry["nass"] = nass[slug]
            pname = self._pinksheet_name(slug)
            if pname and pname in pink:
                entry["pinksheet"] = {**pink[pname], "series": pname,
                                      "label": "World Bank Pink Sheet"}
            rname = self._retail_name(slug)
            if rname and rname in retail:
                entry["retail"] = {**retail[rname], "item": rname,
                                   "label": "BLS US retail average"}
            if entry:
                commodities[slug] = entry

        return {
            "note": ("Per-commodity real series by source; a missing source "
                     "means no genuine series exists in the local data."),
            "commodities": commodities,
            "catalogs": {"pinksheet": pink, "retail": retail, "faostat": faostat},
        }

    def get_source_history(self, commodity: str, source: str) -> Dict:
        """One commodity's series from a specific source (real rows only)."""
        slug = commodity.lower().strip()
        conn = self._connect()
        try:
            cur = conn.cursor()
            if source == "nass":
                cur.execute(
                    "SELECT year, AVG(numeric_value) v, MIN(unit) unit, COUNT(*) n "
                    "FROM wasde_data WHERE commodity = ? "
                    "AND statistic_category='PRICE RECEIVED' AND agg_level='NATIONAL' "
                    "AND freq_desc='ANNUAL' AND numeric_value IS NOT NULL "
                    "GROUP BY year ORDER BY year", (slug.upper(),))
                rows = cur.fetchall()
                if not rows:
                    # some series publish only MONTHLY rows — average those
                    cur.execute(
                        "SELECT year, AVG(numeric_value) v, MIN(unit) unit, COUNT(*) n "
                        "FROM wasde_data WHERE commodity = ? "
                        "AND statistic_category='PRICE RECEIVED' AND agg_level='NATIONAL' "
                        "AND numeric_value IS NOT NULL "
                        "GROUP BY year ORDER BY year", (slug.upper(),))
                    rows = cur.fetchall()
                data = [{"date": f"{r['year']}-07-01", "year": r["year"],
                         "price": round(r["v"], 4)} for r in rows]
                unit = rows[0]["unit"] if rows else None
                label = "USDA NASS farm-gate price (annual avg)"
            elif source == "pinksheet":
                name = self._pinksheet_name(slug) or commodity
                cur.execute(
                    "SELECT date, price, unit FROM global_prices "
                    "WHERE source='World Bank Pink Sheet' AND commodity = ? "
                    "ORDER BY date", (name,))
                rows = cur.fetchall()
                data = [{"date": str(r["date"])[:10],
                         "year": int(str(r["date"])[:4]),
                         "price": r["price"]} for r in rows]
                unit = rows[0]["unit"] if rows else None
                label = f"World Bank Pink Sheet — {name}"
            elif source == "retail":
                name = self._retail_name(slug) or commodity
                cur.execute(
                    "SELECT date, price, unit FROM retail_prices "
                    "WHERE source='BLS AP' AND food_item = ? ORDER BY date", (name,))
                rows = cur.fetchall()
                data = [{"date": str(r["date"])[:10],
                         "year": int(str(r["date"])[:4]),
                         "price": r["price"]} for r in rows]
                unit = rows[0]["unit"] if rows else None
                label = f"BLS US retail average — {name}"
            else:
                return {"status": "bad_source", "source": source}
        finally:
            conn.close()

        if not data:
            return {"commodity": slug, "source": source, "has_history": False,
                    "data_points": 0, "data": [],
                    "note": "No series for this commodity in this source."}
        return {
            "commodity": slug, "source": source, "has_history": True,
            "label": label, "unit": unit, "data_points": len(data),
            "date_range": {"start": data[0]["date"], "end": data[-1]["date"]},
            "data": data,
        }

    def get_producer_price_items(self, min_countries: int = 5) -> List[Dict]:
        """FAOSTAT items with per-country producer-price coverage."""
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT commodity AS item, COUNT(DISTINCT country) n_countries, "
                "COUNT(*) n_obs, MIN(date) s, MAX(date) e "
                "FROM global_prices WHERE source='FAOSTAT' "
                "GROUP BY commodity HAVING n_countries >= ? "
                "ORDER BY n_countries DESC, item", (min_countries,))
            return [{"item": r["item"], "n_countries": r["n_countries"],
                     "n_obs": r["n_obs"],
                     "year_start": int(str(r["s"])[:4]),
                     "year_end": int(str(r["e"])[:4])} for r in cur.fetchall()]
        finally:
            conn.close()

    def get_producer_price_series(self, item: str) -> Dict:
        """All (country, year, USD/tonne) rows for one FAOSTAT item."""
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT country, CAST(strftime('%Y', date) AS INTEGER) year, "
                "AVG(price) value FROM global_prices "
                "WHERE source='FAOSTAT' AND commodity = ? "
                "GROUP BY country, year ORDER BY country, year", (item,))
            rows = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()
        if not rows:
            return {"status": "data_unavailable", "item": item}
        countries = sorted({r["country"] for r in rows})
        return {
            "item": item, "unit": "USD/tonne",
            "countries": countries, "n_obs": len(rows),
            "year_range": {"start": min(r["year"] for r in rows),
                           "end": max(r["year"] for r in rows)},
            "data": [{"region": r["country"], "year": r["year"],
                      "value": r["value"]} for r in rows],
            "source": "FAOSTAT producer prices (local database, offline)",
        }

    def get_state_price_series(self, commodity: str) -> Dict:
        """USDA NASS state-level PRICE RECEIVED annual series per state."""
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT location AS region, year, AVG(numeric_value) value, "
                "MIN(unit) unit FROM wasde_data "
                "WHERE commodity = ? AND statistic_category='PRICE RECEIVED' "
                "AND agg_level='STATE' AND numeric_value IS NOT NULL "
                "GROUP BY location, year ORDER BY location, year",
                (commodity.upper(),))
            rows = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()
        if not rows:
            return {"status": "data_unavailable", "commodity": commodity}
        states = sorted({r["region"] for r in rows})
        return {
            "commodity": commodity.lower(), "unit": rows[0]["unit"],
            "regions": states, "n_obs": len(rows),
            "year_range": {"start": min(r["year"] for r in rows),
                           "end": max(r["year"] for r in rows)},
            "data": [{"region": r["region"], "year": r["year"],
                      "value": r["value"]} for r in rows],
            "source": "USDA NASS state farm-gate prices (local database, offline)",
        }

    def get_global_indices(self) -> Dict:
        """Pink Sheet index series + FAO per-country food-CPI catalog."""
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT commodity, unit, COUNT(*) n, MIN(date) s, MAX(date) e "
                "FROM global_prices WHERE source='World Bank Pink Sheet' "
                "AND (unit LIKE '%=100%' OR unit LIKE '%= 100%' "
                "     OR unit LIKE '%index%' OR unit LIKE '%Index%') "
                "GROUP BY commodity ORDER BY commodity")
            pink_idx = [{"series": r["commodity"], "unit": r["unit"],
                         "points": r["n"], "start": str(r["s"])[:10],
                         "end": str(r["e"])[:10]} for r in cur.fetchall()]
            cur.execute(
                "SELECT country, COUNT(*) n, MIN(date) s, MAX(date) e "
                "FROM global_prices WHERE source='FAOSTAT CPI' "
                "GROUP BY country ORDER BY country")
            cpi = [{"country": r["country"], "points": r["n"],
                    "start": str(r["s"])[:10], "end": str(r["e"])[:10]}
                   for r in cur.fetchall()]
        finally:
            conn.close()
        return {"pinksheet_indices": pink_idx, "fao_food_cpi_countries": cpi}

    def get_pinksheet_series(self, name: str) -> Dict:
        """One Pink Sheet monthly series (commodity or index) by exact name."""
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT date, price, unit FROM global_prices "
                "WHERE source='World Bank Pink Sheet' AND commodity = ? "
                "ORDER BY date", (name,))
            rows = cur.fetchall()
        finally:
            conn.close()
        if not rows:
            return {"status": "data_unavailable", "series": name}
        return {
            "series": name, "unit": rows[0]["unit"],
            "data_points": len(rows),
            "data": [{"date": str(r["date"])[:10], "value": r["price"]}
                     for r in rows],
            "source": "World Bank Pink Sheet (local database, offline)",
        }

    def get_country_cpi_series(self, country: str) -> Dict:
        """One country's monthly FAO food CPI (2015=100)."""
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT date, price FROM global_prices "
                "WHERE source='FAOSTAT CPI' AND country = ? ORDER BY date",
                (country,))
            rows = cur.fetchall()
        finally:
            conn.close()
        if not rows:
            return {"status": "data_unavailable", "country": country}
        return {
            "country": country, "unit": "index 2015=100",
            "data_points": len(rows),
            "data": [{"date": str(r["date"])[:10], "value": r["price"]}
                     for r in rows],
            "source": "FAOSTAT consumer food price indices (local, offline)",
        }
