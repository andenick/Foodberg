"""
Composite Food Price Index Calculator

Builds composite indices from FAO sub-indices and BLS CPI food data.

Two index families:
1. FAO-based global indices (1990-present, base 2014-2016=100)
   - Passes through FAO's own published meat, dairy, cereals, oils, sugar
     sub-indices AND FAO's own published headline Food Price Index
   - Separately publishes a Foodberg-weighted composite under a Foodberg name

2. BLS-based US indices (2015-present, base 1982-1984=100)
   - Uses BLS CPI food sub-components
   - Cereals & Bakery, Meats/Poultry/Fish/Eggs, Fruits & Veg, Dairy, Food Away
   - This is a Foodberg construction, not a BLS publication (see below)


RECOMPUTE-VS-PUBLISH RULE (P0-4, 2026-07-24)
--------------------------------------------
A series that carries a publisher's name must carry that publisher's published
numbers. Before 2026-07-24 the `fao_overall` category held a Foodberg
recomputation - a fixed-weight average of five FAO sub-indices - while the
chart labelled that line "FAO Overall". It disagreed with FAO's actual Food
Price Index in **405 of 431 months**, by up to **4.05 index points**
(2025-11: Foodberg 124.5 vs FAO's published 125.1). FAO chains its index with
2014-2016 trade-share weights that vary by year; a fixed-weight average cannot
reproduce it and must not borrow its name.

Resolution: `fao_overall` now carries FAO's **published** Food Price Index
verbatim. The category key, base period and date range are unchanged, so the
frontend contract (`FoodPriceIndex.tsx` keys off `fao_overall`) is untouched -
only the numbers become FAO's own. The fixed-weight recomputation is retained
in full under the category `foodberg_global_composite`, which claims no
publisher's name.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# FAO component weights (from FAO methodology)
FAO_WEIGHTS = {
    "meat": 0.348,
    "cereals": 0.272,
    "dairy": 0.173,
    "oils": 0.135,
    "sugar": 0.072,
}

# BLS CPI food component weights (approximate US consumer expenditure shares)
BLS_WEIGHTS = {
    "CUUR0000SAF112": 0.30,  # Meats, Poultry, Fish, Eggs
    "CUUR0000SAF111": 0.20,  # Cereals and Bakery
    "CUUR0000SAF113": 0.18,  # Fruits and Vegetables
    "CUUR0000SEFJ": 0.15,    # Dairy
    "CUUR0000SEFV": 0.17,    # Food Away from Home
}

BLS_SERIES_NAMES = {
    "CUUR0000SAF112": "meat",
    "CUUR0000SAF111": "cereals",
    "CUUR0000SAF113": "produce",
    "CUUR0000SEFJ": "dairy",
    "CUUR0000SEFV": "food_away",
}


def compute_all_indices(db_path: Optional[str] = None, conn=None):
    """
    Compute and store all composite food price indices.

    Produces monthly records for:
    - fao_meat, fao_dairy, fao_cereals, fao_oils, fao_sugar
        FAO's own published sub-indices, passed through verbatim.
    - fao_overall
        FAO's own published headline Food Price Index, passed through
        verbatim (see the recompute-vs-publish note in the module docstring).
    - foodberg_global_composite
        Foodberg's fixed-weight average of the five FAO sub-indices. A
        Foodberg construction; deliberately does not carry FAO's name.
    - bls_overall
        Foodberg's weighted composite of BLS CPI food components. A Foodberg
        construction; BLS publishes no such index.

    Every write is an UPSERT, so re-running this refreshes stale values and
    stale `computed_at` stamps instead of silently skipping them. Prior to
    2026-07-24 it skipped any (date, category) that already existed, which is
    why `composite_indices.computed_at` was frozen at 2026-03-28 while the
    underlying source tables moved on.

    Args:
        db_path: path to foodberg.db. Ignored when `conn` is supplied.
        conn:    an open sqlite3 connection to reuse. When supplied, the
                 caller owns commit/close (used by rebake_history.py so the
                 rebake runs in one transaction scope).
    """
    owns_conn = conn is None
    if owns_conn:
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / "data" / "foodberg.db")
        conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    stats = {"inserted": 0, "updated": 0, "unchanged": 0}

    # --- FAO-based indices ---
    print("Refreshing FAO-published indices + Foodberg global composite...")
    fao_data = _load_fao_data(cursor)
    _accumulate(stats, _store_fao_indices(cursor, fao_data))

    # --- BLS-based US index ---
    print("Refreshing Foodberg BLS-based US composite index...")
    bls_data = _load_bls_data(cursor)
    _accumulate(stats, _store_bls_index(cursor, bls_data))

    conn.commit()
    if owns_conn:
        conn.close()

    print(
        f"\nComposite index refresh complete: "
        f"{stats['inserted']} inserted, {stats['updated']} updated, "
        f"{stats['unchanged']} unchanged"
    )
    return stats


def _accumulate(total: Dict[str, int], part: Dict[str, int]) -> None:
    for k in ("inserted", "updated", "unchanged"):
        total[k] += part.get(k, 0)


def _load_fao_data(cursor) -> Dict[str, List]:
    """Load FAO sub-index data grouped by category and date"""
    categories = {}
    cursor.execute("""
        SELECT commodity, date, price
        FROM global_prices
        WHERE source = 'FAO'
        ORDER BY date
    """)
    for commodity, date_str, value in cursor.fetchall():
        # Map commodity name to short category
        cat = _fao_commodity_to_category(commodity)
        if cat not in categories:
            categories[cat] = {}
        # Store by date
        date_key = date_str[:7]  # YYYY-MM
        categories[cat][date_key] = value

    return categories


def _fao_commodity_to_category(commodity: str) -> str:
    """Map FAO commodity name to short category"""
    lower = commodity.lower()
    if "meat" in lower:
        return "meat"
    elif "dairy" in lower:
        return "dairy"
    elif "cereal" in lower:
        return "cereals"
    elif "oil" in lower:
        return "oils"
    elif "sugar" in lower:
        return "sugar"
    elif "overall" in lower or "food" in lower:
        return "food"
    return "other"


def _store_fao_indices(cursor, fao_data: Dict) -> Dict[str, int]:
    """
    Store FAO's published sub-indices and headline index verbatim, plus the
    Foodberg fixed-weight composite under its own (non-FAO) name.
    """
    stats = {"inserted": 0, "updated": 0, "unchanged": 0}
    now = datetime.utcnow().isoformat()
    missing_published = 0

    # Get all dates that have data for at least 3 categories
    all_dates = set()
    for cat_data in fao_data.values():
        all_dates.update(cat_data.keys())

    for date_key in sorted(all_dates):
        date_str = f"{date_key}-01"

        # --- FAO's own published sub-indices, verbatim ---
        for cat in ["meat", "dairy", "cereals", "oils", "sugar"]:
            if cat in fao_data and date_key in fao_data[cat]:
                value = fao_data[cat][date_key]
                _accumulate(stats, _upsert_index(
                    cursor, date_str, f"fao_{cat}", value,
                    json.dumps({
                        "series": "published",
                        "publisher": "FAO",
                        "publisher_series": f"FAO Food Price Index - {cat.title()}",
                        "raw_value": value,
                    }),
                    "2014-2016", now))

        # --- FAO's own published headline Food Price Index, verbatim ---
        # P0-4: this category is named after FAO, so it must carry FAO's number.
        published_overall = fao_data.get("food", {}).get(date_key)
        if published_overall is not None:
            _accumulate(stats, _upsert_index(
                cursor, date_str, "fao_overall", published_overall,
                json.dumps({
                    "series": "published",
                    "publisher": "FAO",
                    "publisher_series": "FAO Food Price Index (headline)",
                    "recomputed": False,
                    "note": "FAO's published figure, passed through verbatim.",
                }),
                "2014-2016", now))
        else:
            missing_published += 1

        # --- Foodberg's fixed-weight composite, under a Foodberg name ---
        components = {}
        for cat in FAO_WEIGHTS:
            if cat in fao_data and date_key in fao_data[cat]:
                components[cat] = fao_data[cat][date_key]

        if len(components) >= 4:  # Need most categories
            weight_sum = sum(FAO_WEIGHTS[cat] for cat in components)
            overall = sum(FAO_WEIGHTS[cat] * val for cat, val in components.items())
            overall = overall / weight_sum if weight_sum > 0 else 0

            _accumulate(stats, _upsert_index(
                cursor, date_str, "foodberg_global_composite", round(overall, 2),
                json.dumps({
                    "series": "recomputed",
                    "publisher": "Foodberg",
                    "method": "fixed-weight average of FAO sub-indices",
                    "weights": FAO_WEIGHTS,
                    "components": components,
                    "note": ("Foodberg construction. NOT the FAO Food Price "
                             "Index; see fao_overall for FAO's published figure."),
                }),
                "2014-2016", now))

    if missing_published:
        logger.warning(
            "%d month(s) had FAO sub-indices but no published headline index; "
            "fao_overall left unwritten for those months rather than recomputed.",
            missing_published,
        )
    print(f"  FAO indices: {stats}")
    return stats


def _load_bls_data(cursor) -> Dict[str, Dict]:
    """Load BLS CPI food component data"""
    series_data = {}
    cursor.execute("""
        SELECT series_id, date, value
        FROM economic_indicators
        WHERE source = 'BLS'
        AND series_id IN ('CUUR0000SAF112', 'CUUR0000SAF111', 'CUUR0000SAF113',
                          'CUUR0000SEFJ', 'CUUR0000SEFV')
        ORDER BY date
    """)
    for series_id, date_str, value in cursor.fetchall():
        if series_id not in series_data:
            series_data[series_id] = {}
        date_key = date_str[:7]
        series_data[series_id][date_key] = value

    return series_data


def _store_bls_index(cursor, bls_data: Dict) -> Dict[str, int]:
    """
    Compute and store Foodberg's US food price composite index from BLS CPI
    food components.

    NOTE: `bls_overall` is a Foodberg construction using approximate US
    consumer expenditure shares - BLS publishes no such index. The category
    key is retained because the frontend depends on it, but the label shown to
    users must not imply BLS authorship (tracked separately from P0-4).
    """
    stats = {"inserted": 0, "updated": 0, "unchanged": 0}
    now = datetime.utcnow().isoformat()

    # Get all dates
    all_dates = set()
    for series_values in bls_data.values():
        all_dates.update(series_values.keys())

    for date_key in sorted(all_dates):
        date_str = f"{date_key}-01"

        components = {}
        for series_id, weight in BLS_WEIGHTS.items():
            if series_id in bls_data and date_key in bls_data[series_id]:
                name = BLS_SERIES_NAMES.get(series_id, series_id)
                components[name] = bls_data[series_id][date_key]

        if len(components) >= 3:  # Need most categories
            overall = sum(
                BLS_WEIGHTS[sid] * bls_data[sid][date_key]
                for sid in BLS_WEIGHTS
                if sid in bls_data and date_key in bls_data[sid]
            )
            weight_sum = sum(
                BLS_WEIGHTS[sid]
                for sid in BLS_WEIGHTS
                if sid in bls_data and date_key in bls_data[sid]
            )
            overall = overall / weight_sum if weight_sum > 0 else 0

            _accumulate(stats, _upsert_index(
                cursor, date_str, "bls_overall", round(overall, 2),
                json.dumps({
                    "series": "recomputed",
                    "publisher": "Foodberg",
                    "method": ("weighted average of BLS CPI food components, "
                               "approximate US consumer expenditure shares"),
                    "weights": BLS_WEIGHTS,
                    "components": components,
                    "note": ("Foodberg construction. BLS publishes no overall "
                             "food price index under this definition."),
                }),
                "1982-1984", now))

    print(f"  BLS US index: {stats}")
    return stats


def _upsert_index(cursor, date_str: str, category: str, value: float,
                  components_json: str, base_period: str,
                  computed_at: str) -> Dict[str, int]:
    """
    Insert or update a composite index record.

    Returns a one-hot dict of {inserted|updated|unchanged}. An existing row
    whose value or components differ is UPDATED - the previous implementation
    skipped it, which froze `composite_indices` at its first computation
    (P0-5) and kept the wrong `fao_overall` values alive (P0-4).
    """
    row = cursor.execute(
        "SELECT id, index_value, components_json, base_period "
        "FROM composite_indices WHERE date = ? AND category = ?",
        (date_str, category)
    ).fetchone()

    if row is None:
        cursor.execute(
            "INSERT INTO composite_indices "
            "(date, category, index_value, components_json, base_period, computed_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (date_str, category, value, components_json, base_period, computed_at)
        )
        return {"inserted": 1}

    row_id, old_value, old_components, old_base = row
    if (old_value == value and old_components == components_json
            and old_base == base_period):
        return {"unchanged": 1}

    cursor.execute(
        "UPDATE composite_indices SET index_value = ?, components_json = ?, "
        "base_period = ?, computed_at = ? WHERE id = ?",
        (value, components_json, base_period, computed_at, row_id)
    )
    return {"updated": 1}
