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

    # Retail item -> the PPI series in `economic_indicators` that measures the
    # SAME good one step earlier in the chain (farm/producer gate rather than
    # the grocery shelf). Deliberately tiny, explicit and hand-verified: a
    # farm->retail wedge is only meaningful when the two series really do track
    # the same commodity, so this is an allow-list, never a fuzzy match. An item
    # with no entry here reports `wedge.ppi: null` — an honest absence.
    #   'Tomatoes, field grown' <-> WPU01130217 "PPI - Farm Products: Tomatoes"
    #   is the pair named in FOODBERG_CHEF_FIRST_PLAN_20260724.md §1.1; both
    #   sides were ingested by Technical/scripts/ingest_bls_monthly_series.py.
    # The mapped series is looked up in the database before it is emitted, so a
    # link to a series that is not actually loaded degrades to null instead of
    # inventing a wedge.
    RETAIL_PPI_LINKS: Dict[str, str] = {
        "Tomatoes, field grown": "WPU01130217",
    }

    # Publisher provenance per source key. The landing URLs are the same public
    # pages Technical/scripts/reality_audit.py resolves for these sources.
    # `retrieval_url` is a publisher page, not an API call: everything Foodberg
    # serves comes from the baked local database, offline.
    SOURCE_PROVENANCE: Dict[str, Dict[str, str]] = {
        "retail": {
            "publisher": "U.S. Bureau of Labor Statistics",
            "programme": "Average Price Data (AP)",
            "retrieval_url": "https://www.bls.gov/cpi/data.htm",
            "geography": "U.S. city average",
            "licence": "U.S. Government work (public domain)",
            "series_id_note": (
                "retail_prices stores no publisher series id; the BLS item name "
                "is the key. The APU series ids live in Robin's canonical store "
                "(Council/Robin/DATA/BLS_AP/)."),
        },
        "nass": {
            "publisher": "USDA National Agricultural Statistics Service",
            "programme": "Quick Stats - PRICE RECEIVED",
            "retrieval_url": "https://quickstats.nass.usda.gov/",
            "geography": "United States (national)",
            "licence": "U.S. Government work (public domain)",
        },
        "pinksheet": {
            "publisher": "World Bank",
            "programme": "Commodity Markets 'Pink Sheet' (Monthly)",
            "retrieval_url": (
                "https://www.worldbank.org/en/research/commodity-markets"),
            "geography": "global",
            "licence": "CC BY 4.0",
        },
        "av": {
            "publisher": "Alpha Vantage (commercial aggregator)",
            "programme": "Commodities API (continuous contract)",
            "retrieval_url": (
                "https://www.alphavantage.co/documentation/#commodities"),
            "geography": "global",
            "licence": "UNRESOLVED - redistribution terms not established",
        },
        "wholesale": {
            "publisher": "USDA Agricultural Marketing Service",
            "programme": "Market News - terminal market prices (MARS API v3.1)",
            "retrieval_url": (
                "https://marsapi.ams.usda.gov/services/v3.1/reports"),
            "geography": "US terminal markets",
            "licence": "U.S. Government work (public domain)",
        },
    }

    # Order in which sources are listed, and therefore which one is treated as
    # the item's PRIMARY source for the headline unit and provenance: the
    # closest to a kitchen first (US retail shelf), the furthest last (global
    # farm-gate / futures).
    SOURCE_ORDER = ("retail", "nass", "pinksheet", "av")

    def _pinksheet_name(self, slug: str) -> Optional[str]:
        return self.COMMODITY_LINKS.get(slug, {}).get("pinksheet")

    def _retail_name(self, slug: str) -> Optional[str]:
        """Resolve a commodity slug to a BLS AP `retail_prices.food_item`.

        Two-step, because COMMODITY_LINKS is a hand-written allow-list that only
        ever covered 11 of the 47 BLS AP items (Tier 0 defect: 36 items — every
        vegetable including tomatoes — were orphaned because they have no USDA
        NASS parent commodity to hang off).

        1. The curated link, where one exists (it maps a NASS slug such as
           `cattle` onto the BLS item "Ground beef, 100% beef").
        2. Otherwise the auto-derived slug of the BLS item itself, so every AP
           item is addressable in its own right. See _retail_slug().
        """
        linked = self.COMMODITY_LINKS.get(slug, {}).get("retail")
        if linked:
            return linked
        return self._retail_index().get(slug)

    # -- BLS AP auto-surfacing (Tier 0) --------------------------------------
    # Every BLS Average Price item becomes a first-class, addressable commodity
    # instead of being reachable only when some NASS commodity happened to be
    # hand-linked to it.

    @staticmethod
    def _retail_slug(food_item: str) -> str:
        """'Tomatoes, field grown' -> 'tomatoes-field-grown'.

        Deterministic and reversible-enough to be a URL slug. Keeping the full
        item name in the slug (rather than truncating to the head noun) avoids
        collisions between e.g. 'Bread, white, pan' and 'Bread, whole wheat,
        pan', and still substring-matches a search for 'tomato' or 'bread'.
        """
        out = []
        prev_dash = False
        for ch in str(food_item).lower():
            if ch.isalnum():
                out.append(ch)
                prev_dash = False
            elif not prev_dash:
                out.append("-")
                prev_dash = True
        return "".join(out).strip("-")

    def _retail_index(self) -> Dict[str, str]:
        """slug -> BLS AP food_item, for every item present in retail_prices.

        Cached on the instance; the underlying table is baked into the image and
        cannot change at runtime.
        """
        cached = getattr(self, "_retail_index_cache", None)
        if cached is not None:
            return cached
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT DISTINCT food_item FROM retail_prices WHERE source='BLS AP'")
            index = {self._retail_slug(r["food_item"]): r["food_item"]
                     for r in cur.fetchall()}
        except sqlite3.Error:
            index = {}
        finally:
            conn.close()
        self._retail_index_cache = index
        return index

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

    # -- Frequency normalization (Wave B) ------------------------------------
    # Every source spells its own frequency differently, and one of them
    # ("annual+monthly", USDA NASS) is not a frequency at all — it describes the
    # mix of rows stored, not the cadence of the series the API actually serves.
    # A client cannot filter, badge, or resample on strings like that, so the
    # API emits a NORMALIZED `freq` alongside the original `frequency` string.
    # The original key is never removed: the shipped frontend reads it.
    #
    # Exactly one of daily | weekly | monthly | annual, or None when the stored
    # string names no cadence this vocabulary covers. None is an honest "not
    # classifiable", never a guess.

    CANONICAL_FREQUENCIES = ("daily", "weekly", "monthly", "annual")

    _FREQUENCY_ALIASES: Dict[str, Optional[str]] = {
        "daily": "daily",
        "daily (business days)": "daily",
        "business daily": "daily",
        "weekly": "weekly",
        "monthly": "monthly",
        "quarterly": None,          # no quarterly price series is served here
        "annual": "annual",
        "annually": "annual",
        "yearly": "annual",
        # USDA NASS PRICE RECEIVED keeps ANNUAL and MONTHLY rows for the same
        # national series. get_source_history() serves the ANNUAL series (it
        # falls back to averaging monthly rows into years only when a commodity
        # publishes no annual row at all), so the cadence a client receives is
        # annual in both cases.
        "annual+monthly": "annual",
        "annual/monthly": "annual",
    }

    # The cadence of each source as Foodberg SERVES it. Used where no stored
    # frequency string exists to normalize (USDA AMS wholesale rows carry no
    # frequency column — they are one row per commodity/package/city/report day).
    SOURCE_FREQUENCY: Dict[str, str] = {
        "av": "monthly",            # Alpha Vantage monthly continuous contract
        "nass": "annual",           # USDA NASS PRICE RECEIVED, national annual
        "pinksheet": "monthly",     # World Bank Pink Sheet monthly
        "retail": "monthly",        # BLS Average Price monthly
        "wholesale": "daily",       # USDA AMS terminal markets, per report day
    }

    @classmethod
    def normalize_frequency(cls, raw: Optional[str]) -> Optional[str]:
        """Map a stored frequency string onto the canonical vocabulary.

        Returns 'daily' | 'weekly' | 'monthly' | 'annual', or None when the
        input names no cadence in that vocabulary.
        """
        if raw is None:
            return None
        key = str(raw).strip().lower()
        if not key:
            return None
        if key in cls._FREQUENCY_ALIASES:
            return cls._FREQUENCY_ALIASES[key]
        if key in cls.CANONICAL_FREQUENCIES:
            return key
        return None

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
        # Wave B: every entry also carries a NORMALIZED `freq`
        # (daily|weekly|monthly|annual) so a client can badge and filter on
        # cadence without parsing prose. `frequency` is left untouched.
        for source_key, catalog in (("av", av), ("nass", nass),
                                    ("pinksheet", pink), ("retail", retail)):
            catalog_end = max(
                (e["end"] for e in catalog.values() if e.get("end")),
                default=None)
            for entry in catalog.values():
                entry["liveness"] = self._liveness(entry.get("end"), catalog_end)
                entry["freq"] = (self.normalize_frequency(entry.get("frequency"))
                                 or self.SOURCE_FREQUENCY.get(source_key))

        # Assemble per-commodity source map over the NASS commodity universe
        # plus anything AV covers.
        commodities: Dict[str, Dict] = {}
        display_names: Dict[str, str] = {}
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
            rname = self.COMMODITY_LINKS.get(slug, {}).get("retail")
            if rname and rname in retail:
                entry["retail"] = {**retail[rname], "item": rname,
                                   "label": "BLS US retail average"}
            if entry:
                commodities[slug] = entry

        # TIER 0 — surface EVERY BLS AP item, not just the hand-linked ones.
        #
        # Before this block the browsable universe was the USDA NASS commodity
        # list plus a 20-entry hand-written allow-list (COMMODITY_LINKS). BLS
        # retail could only appear as a source *tab* on a commodity that already
        # had a NASS parent, so 36 of the 47 AP items — every vegetable, all the
        # bakery/dairy/pantry items, and "Tomatoes, field grown" (552 monthly
        # observations, 1980-01 → 2026-06) — were in the database and
        # unreachable from the UI. Each unlinked AP item now becomes a
        # first-class commodity keyed by its own slug.
        #
        # Items already carried by a curated link (e.g. "Ground beef, 100% beef"
        # under `cattle`) are NOT duplicated — their NASS parent shows strictly
        # more sources.
        linked_items = {v["retail"] for v in self.COMMODITY_LINKS.values()
                        if "retail" in v}
        for slug, item in sorted(self._retail_index().items()):
            if item in linked_items or item not in retail or slug in commodities:
                continue
            commodities[slug] = {"retail": {**retail[item], "item": item,
                                            "label": "BLS US retail average"}}
            display_names[slug] = item

        return {
            "note": ("Per-commodity real series by source; a missing source "
                     "means no genuine series exists in the local data."),
            "commodities": commodities,
            # Human-readable name for slugs derived from a publisher's own item
            # label (BLS AP). Slugs absent from this map are plain commodity
            # names and the UI title-cases them.
            "display_names": display_names,
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

    # -- Detail rail (Wave B) ------------------------------------------------

    @staticmethod
    def _head_noun(item: str) -> str:
        """'Tomatoes, field grown' -> 'Tomatoes'; 'Bananas' -> 'Bananas'.

        The BLS AP item convention is `<commodity>, <qualifiers>`, so the text
        before the first comma is the commodity itself. Used ONLY to propose a
        candidate USDA AMS `commodity`, which is then verified against the table
        before anything is emitted.
        """
        return str(item).split(",")[0].strip()

    @staticmethod
    def _region_of(item: str) -> Optional[str]:
        """'Tomatoes, field grown (Midwest)' -> 'Midwest'."""
        if item.endswith(")") and "(" in item:
            return item[item.rindex("(") + 1:-1].strip() or None
        return None

    def get_price_detail(self, slug: str) -> Dict:
        """Everything the explorer's detail rail needs for ONE item, in one call.

        Assembles, for a commodity slug:
          sources     every source carrying the item, each with a NORMALIZED
                      frequency (daily|weekly|monthly|annual), unit, span and
                      liveness verdict
          regional    sibling series discovered from the `<item> (<Region>)`
                      naming convention in retail_prices - not a hardcoded list
          wedge       farm -> wholesale -> retail for the same good, emitted
                      ONLY where each leg genuinely exists
          provenance  publisher, series id or item key, retrieval URL, geography
                      and unit of the primary source

        Every `null` means "checked, genuinely absent" - `wedge.basis` says why
        for each leg, so absence is never confused with "not looked at".
        Returns {'status': 'unknown_commodity'} for a slug that is not in the
        coverage universe; the HTTP layer turns that into a 404.
        """
        slug = str(slug).lower().strip()
        coverage = self.get_price_coverage()
        entry = coverage["commodities"].get(slug)
        if entry is None:
            return {
                "status": "unknown_commodity",
                "slug": slug,
                "reason": ("No commodity with this slug exists in the local "
                           "price coverage universe."),
                "n_known_slugs": len(coverage["commodities"]),
            }

        label = coverage["display_names"].get(slug) or slug.replace("-", " ").title()
        retail_item = entry.get("retail", {}).get("item")

        conn = self._connect()
        try:
            cur = conn.cursor()

            # -- units per source, read from the rows actually served ---------
            units: Dict[str, Optional[str]] = {}
            if "retail" in entry:
                units["retail"] = entry["retail"].get("unit")
            if "pinksheet" in entry:
                units["pinksheet"] = entry["pinksheet"].get("unit")
            if "av" in entry:
                row = cur.execute(
                    "SELECT MIN(unit) u FROM global_prices "
                    "WHERE source='Alpha Vantage' AND indicator_code = ?",
                    (("CORN" if slug == "maize" else slug).upper(),)).fetchone()
                units["av"] = row["u"] if row else None
            if "nass" in entry:
                # Same filters get_source_history() uses for the annual series,
                # so the reported unit is the unit of the series actually served.
                row = cur.execute(
                    "SELECT MIN(unit) u FROM wasde_data WHERE commodity = ? "
                    "AND statistic_category='PRICE RECEIVED' "
                    "AND agg_level='NATIONAL' AND freq_desc='ANNUAL' "
                    "AND numeric_value IS NOT NULL", (slug.upper(),)).fetchone()
                unit = row["u"] if row else None
                if unit is None:
                    row = cur.execute(
                        "SELECT MIN(unit) u FROM wasde_data WHERE commodity = ? "
                        "AND statistic_category='PRICE RECEIVED' "
                        "AND agg_level='NATIONAL' AND numeric_value IS NOT NULL",
                        (slug.upper(),)).fetchone()
                    unit = row["u"] if row else None
                units["nass"] = unit

            # -- sources -------------------------------------------------------
            sources: List[Dict[str, Any]] = []
            for key in self.SOURCE_ORDER:
                src = entry.get(key)
                if not src:
                    continue
                item: Dict[str, Any] = {
                    "key": key,
                    "label": src.get("label") or key,
                    "frequency": (self.normalize_frequency(src.get("frequency"))
                                  or self.SOURCE_FREQUENCY[key]),
                    "frequency_as_stored": src.get("frequency"),
                    "unit": units.get(key),
                    "points": src.get("points"),
                    "start": src.get("start"),
                    "end": src.get("end"),
                    "liveness": src.get("liveness"),
                }
                if key == "nass":
                    item["n_years"] = src.get("n_years")
                    item["points_note"] = (
                        "`points` counts every stored PRICE RECEIVED "
                        "observation (annual and monthly rows); the national "
                        "series served by /api/prices/source is annual, one "
                        "point per year (`n_years`).")
                if key == "retail" and src.get("item"):
                    item["series"] = src["item"]
                if key == "pinksheet" and src.get("series"):
                    item["series"] = src["series"]
                sources.append(item)

            primary = sources[0]["key"] if sources else None

            # -- regional variants --------------------------------------------
            # Discovered from the publisher's own naming convention
            # `<base item> (<Region>)`, so any future regional item is picked up
            # without a code change. Nothing about tomatoes is hardcoded.
            regional: List[Dict[str, Any]] = []
            if retail_item:
                variants = cur.execute(
                    "SELECT food_item, MIN(location) location, MIN(unit) unit, "
                    "COUNT(*) n, MAX(date) e FROM retail_prices "
                    "WHERE source='BLS AP' AND food_item LIKE ? "
                    "AND food_item <> ? GROUP BY food_item ORDER BY food_item",
                    (f"{retail_item} (%)", retail_item)).fetchall()
                for v in variants:
                    region = self._region_of(v["food_item"])
                    if region is None:
                        continue
                    latest = cur.execute(
                        "SELECT date, price FROM retail_prices "
                        "WHERE source='BLS AP' AND food_item = ? "
                        "ORDER BY date DESC LIMIT 1", (v["food_item"],)).fetchone()
                    regional.append({
                        "slug": self._retail_slug(v["food_item"]),
                        "label": v["food_item"],
                        "region": region,
                        "location": v["location"],
                        "unit": v["unit"],
                        "frequency": self.SOURCE_FREQUENCY["retail"],
                        "points": v["n"],
                        "latest": ({"date": str(latest["date"])[:10],
                                    "price": latest["price"]}
                                   if latest else None),
                    })

            # -- wedge: farm -> wholesale -> retail ----------------------------
            wedge: Dict[str, Any] = {"retail": None, "ppi": None,
                                     "wholesale": None}
            basis: Dict[str, str] = {}

            if retail_item:
                latest = cur.execute(
                    "SELECT date, price, unit FROM retail_prices "
                    "WHERE source='BLS AP' AND food_item = ? "
                    "AND location='U.S. city average' "
                    "ORDER BY date DESC LIMIT 1", (retail_item,)).fetchone()
                if latest:
                    wedge["retail"] = {
                        "label": f"BLS US retail average - {retail_item}",
                        "series": retail_item,
                        "unit": latest["unit"],
                        "latest": {"date": str(latest["date"])[:10],
                                   "price": latest["price"]},
                    }
                    basis["retail"] = (
                        f"BLS AP item '{retail_item}', national "
                        f"(location='U.S. city average')")
                else:
                    basis["retail"] = (
                        f"BLS AP item '{retail_item}' has no national row "
                        f"(location='U.S. city average')")
            else:
                basis["retail"] = "no BLS Average Price item carries this commodity"

            ppi_series = self.RETAIL_PPI_LINKS.get(retail_item or "")
            if ppi_series:
                row = cur.execute(
                    "SELECT date, value, indicator_name FROM economic_indicators "
                    "WHERE series_id = ? ORDER BY date DESC LIMIT 1",
                    (ppi_series,)).fetchone()
                if row:
                    wedge["ppi"] = {
                        "series_id": ppi_series,
                        "label": row["indicator_name"],
                        "unit": "index",
                        "unit_note": ("economic_indicators has no unit column; "
                                      "PPI series are index points, not prices, "
                                      "so the wedge is a co-movement comparison, "
                                      "not a margin in dollars."),
                        "latest": {"date": str(row["date"])[:10],
                                   "value": row["value"]},
                    }
                    basis["ppi"] = (f"explicit retail->PPI pair "
                                    f"'{retail_item}' -> {ppi_series}")
                else:
                    basis["ppi"] = (
                        f"retail->PPI pair maps '{retail_item}' to {ppi_series}, "
                        f"but that series is not loaded in economic_indicators")
            else:
                basis["ppi"] = (
                    "no producer-price pair is mapped for this item "
                    "(RETAIL_PPI_LINKS is a hand-verified allow-list; an "
                    "unmapped item reports null rather than a guessed match)")

            # Two candidate names, tried in order, each an EXACT (case-
            # insensitive) match against the AMS `commodity` column and each
            # verified to return rows before anything is emitted:
            #   1. the publisher's full item name  ('Lettuce, iceberg' ->
            #      AMS 'Lettuce, Iceberg')
            #   2. its head noun                   ('Tomatoes, field grown' ->
            #      AMS 'Tomatoes')
            # No substring, prefix, or fuzzy matching is ever attempted: 'Onions,
            # dry yellow' does not become AMS 'Onions, Dry', because those are
            # different pack specifications and the site would be asserting a
            # linkage the publishers never made.
            base_name = retail_item or label
            candidates = [base_name]
            head = self._head_noun(base_name)
            if head and head.lower() != base_name.lower():
                candidates.append(head)
            row = None
            candidate = candidates[-1]
            for name in candidates:
                found = cur.execute(
                    "SELECT commodity, COUNT(*) rows, COUNT(DISTINCT city) cities, "
                    "COUNT(DISTINCT variety) varieties, MAX(report_date) latest "
                    "FROM ams_wholesale_prices WHERE commodity = ? COLLATE NOCASE",
                    (name,)).fetchone()
                if found and found["rows"]:
                    row, candidate = found, name
                    break
            if row and row["rows"]:
                commodity = row["commodity"]
                latest_date = row["latest"]
                # Terminal-market prices are quoted per PACKAGE, and the packages
                # differ (25 lb cartons loose, flats 2 layer, ...). A low/high
                # taken across mixed packages would not be a price range, so the
                # range is confined to the package unit most quoted on the latest
                # report day, and that unit is reported with it.
                unit_row = cur.execute(
                    "SELECT unit, COUNT(*) n FROM ams_wholesale_prices "
                    "WHERE commodity = ? COLLATE NOCASE AND report_date = ? "
                    "AND unit IS NOT NULL GROUP BY unit "
                    "ORDER BY n DESC, unit LIMIT 1",
                    (candidate, latest_date)).fetchone()
                modal_unit = unit_row["unit"] if unit_row else None
                span = cur.execute(
                    "SELECT MIN(low_price) lo, MAX(high_price) hi, COUNT(*) n, "
                    "COUNT(DISTINCT unit) units FROM ams_wholesale_prices "
                    "WHERE commodity = ? COLLATE NOCASE AND report_date = ? "
                    "AND unit IS ?", (candidate, latest_date, modal_unit)
                ).fetchone()
                all_units = cur.execute(
                    "SELECT COUNT(DISTINCT unit) u FROM ams_wholesale_prices "
                    "WHERE commodity = ? COLLATE NOCASE AND report_date = ?",
                    (candidate, latest_date)).fetchone()
                wedge["wholesale"] = {
                    "commodity": commodity,
                    "cities": row["cities"],
                    "rows": row["rows"],
                    "latest_date": str(latest_date)[:10] if latest_date else None,
                    "low": span["lo"] if span else None,
                    "high": span["hi"] if span else None,
                    "unit": modal_unit,
                    "varieties": row["varieties"],
                    "frequency": self.SOURCE_FREQUENCY["wholesale"],
                    "quotes_at_latest_unit": span["n"] if span else 0,
                    "units_at_latest_date": all_units["u"] if all_units else 0,
                    "range_note": (
                        "low/high are the extremes of the quotes carrying the "
                        "most-quoted package unit on the latest report day; "
                        "other package units on the same day are priced "
                        "differently and are not mixed in."),
                }
                how = ("the full item name" if candidate.lower() == base_name.lower()
                       else "the head noun")
                basis["wholesale"] = (
                    f"USDA AMS commodity '{commodity}' matched exactly on "
                    f"{how} of '{base_name}' ('{candidate}') and returns "
                    f"{row['rows']} rows")
            else:
                basis["wholesale"] = (
                    f"no USDA AMS commodity matches "
                    f"{' or '.join(repr(c) for c in candidates)} exactly; no "
                    f"fuzzy or partial linkage is ever made")
            wedge["basis"] = basis

            # -- provenance of the primary source ------------------------------
            if primary:
                reg = dict(self.SOURCE_PROVENANCE[primary])
                if primary == "retail":
                    series_key = retail_item
                    locations = [r["location"] for r in cur.execute(
                        "SELECT DISTINCT location FROM retail_prices "
                        "WHERE source='BLS AP' AND food_item = ?",
                        (retail_item,)).fetchall()]
                    geography = (locations[0] if len(locations) == 1
                                 else reg["geography"])
                elif primary == "pinksheet":
                    series_key = entry["pinksheet"].get("series")
                    geography = reg["geography"]
                elif primary == "av":
                    series_key = "CORN" if slug == "maize" else slug.upper()
                    geography = reg["geography"]
                else:
                    series_key = slug.upper()
                    geography = reg["geography"]
                provenance = {
                    "source_key": primary,
                    "publisher": reg["publisher"],
                    "programme": reg["programme"],
                    "series_id_or_item": series_key,
                    "retrieval_url": reg["retrieval_url"],
                    "geography": geography,
                    "unit": units.get(primary),
                    "licence": reg["licence"],
                    "delivery": ("served from the baked local database; the URL "
                                 "is the publisher's page, not a live call"),
                }
                if reg.get("series_id_note"):
                    provenance["series_id_note"] = reg["series_id_note"]
            else:
                provenance = None
        finally:
            conn.close()

        return {
            "slug": slug,
            "label": label,
            "unit": units.get(primary) if primary else None,
            "primary_source": primary,
            "sources": sources,
            "regional": regional,
            "wedge": wedge,
            "provenance": provenance,
            "note": (
                "One item, every source that genuinely carries it. `unit` is "
                "the primary source's own unit, verbatim - no conversion is "
                "applied here. `frequency` is normalized to "
                "daily|weekly|monthly|annual; `frequency_as_stored` keeps the "
                "publisher's own wording. An empty `regional` list means the "
                "publisher issues no regional variant of this item. Each null "
                "in `wedge` is a checked absence, explained in `wedge.basis`; "
                "the wedge compares different measurement bases (retail $/unit, "
                "PPI index points, wholesale $/package) and is not a margin."),
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
