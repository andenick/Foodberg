"""
Composite Food Price Index Calculator

Builds weighted composite indices from FAO sub-indices and BLS CPI food data.

Two index families:
1. FAO-based global indices (1990-present, base 2014-2016=100)
   - Uses FAO's own meat, dairy, cereals, oils, sugar sub-indices
   - Computes a Foodberg Overall from weighted FAO components

2. BLS-based US indices (2015-present, base 1982-1984=100)
   - Uses BLS CPI food sub-components
   - Cereals & Bakery, Meats/Poultry/Fish/Eggs, Fruits & Veg, Dairy, Food Away
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


def compute_all_indices(db_path: Optional[str] = None):
    """
    Compute and store all composite food price indices.

    Produces monthly records for:
    - fao_meat, fao_dairy, fao_cereals, fao_oils, fao_sugar (direct from FAO)
    - fao_overall (weighted composite of FAO sub-indices)
    - bls_overall (weighted composite of BLS CPI food components)
    """
    if db_path is None:
        db_path = str(Path(__file__).parent.parent / "data" / "foodberg.db")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    total_inserted = 0

    # --- FAO-based indices ---
    print("Computing FAO-based composite indices...")
    fao_data = _load_fao_data(cursor)
    total_inserted += _store_fao_indices(cursor, fao_data)

    # --- BLS-based US index ---
    print("Computing BLS-based US composite index...")
    bls_data = _load_bls_data(cursor)
    total_inserted += _store_bls_index(cursor, bls_data)

    conn.commit()
    conn.close()

    print(f"\nComposite index computation complete: {total_inserted} records stored")
    return total_inserted


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


def _store_fao_indices(cursor, fao_data: Dict) -> int:
    """Store FAO sub-indices and compute weighted overall"""
    inserted = 0
    now = datetime.utcnow().isoformat()

    # Get all dates that have data for at least 3 categories
    all_dates = set()
    for cat_data in fao_data.values():
        all_dates.update(cat_data.keys())

    for date_key in sorted(all_dates):
        date_str = f"{date_key}-01"

        # Store individual FAO sub-indices
        for cat in ["meat", "dairy", "cereals", "oils", "sugar"]:
            if cat in fao_data and date_key in fao_data[cat]:
                value = fao_data[cat][date_key]
                if _insert_index(cursor, date_str, f"fao_{cat}", value,
                                 json.dumps({"source": "FAO", "raw_value": value}),
                                 "2014-2016", now):
                    inserted += 1

        # Compute weighted FAO overall
        components = {}
        for cat, weight in FAO_WEIGHTS.items():
            if cat in fao_data and date_key in fao_data[cat]:
                components[cat] = fao_data[cat][date_key]

        if len(components) >= 4:  # Need most categories
            overall = sum(
                FAO_WEIGHTS[cat] * val
                for cat, val in components.items()
                if cat in FAO_WEIGHTS
            )
            # Normalize: sum of available weights
            weight_sum = sum(FAO_WEIGHTS[cat] for cat in components if cat in FAO_WEIGHTS)
            overall = overall / weight_sum if weight_sum > 0 else 0

            if _insert_index(cursor, date_str, "fao_overall", round(overall, 2),
                             json.dumps(components), "2014-2016", now):
                inserted += 1

    print(f"  FAO indices: {inserted} records")
    return inserted


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


def _store_bls_index(cursor, bls_data: Dict) -> int:
    """Compute and store BLS-based US food price composite index"""
    inserted = 0
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

            if _insert_index(cursor, date_str, "bls_overall", round(overall, 2),
                             json.dumps(components), "1982-1984", now):
                inserted += 1

    print(f"  BLS US index: {inserted} records")
    return inserted


def _insert_index(cursor, date_str: str, category: str, value: float,
                  components_json: str, base_period: str, computed_at: str) -> bool:
    """Insert a composite index record, skip if duplicate"""
    cursor.execute(
        "SELECT id FROM composite_indices WHERE date = ? AND category = ?",
        (date_str, category)
    )
    if cursor.fetchone():
        return False

    cursor.execute(
        """INSERT INTO composite_indices (date, category, index_value, components_json, base_period, computed_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (date_str, category, value, components_json, base_period, computed_at)
    )
    return True
