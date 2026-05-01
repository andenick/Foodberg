"""
Historical USDA Food Data Importer
Imports 85 JSON files from Robin's OTHER_APIS/USDA_FOOD/data/historical/
into the retail_prices table.

Each file contains a commodity with current price, metadata, and ~365 days
of historical daily price + volume data.

Usage:
    cd backend
    python -m database.importers.historical_importer
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.models import RetailPrice
from database.manager import DatabaseManager

logger = logging.getLogger(__name__)

ROBIN_HISTORICAL_PATH = Path(
    "D:/Arcanum/Council/Robin/DATA/OTHER_APIS/USDA_FOOD/data/historical"
)

NON_FOOD_ITEMS = {"gold", "silver", "crude", "heating", "natural"}


class HistoricalImporter:
    """Import Robin's historical USDA_FOOD commodity price data"""

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = Path(data_path) if data_path else ROBIN_HISTORICAL_PATH
        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Robin historical data not found: {self.data_path}"
            )
        self.db_manager = None

    def set_database_manager(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_files(self) -> List[Path]:
        """Find all historical JSON files"""
        return sorted(self.data_path.glob("*.json"))

    def import_all(self, batch_size: int = 500) -> Dict:
        if not self.db_manager:
            raise ValueError("Database manager not set")

        files = self.get_files()

        stats = {
            "total_files": len(files),
            "total_records": 0,
            "imported": 0,
            "skipped": 0,
            "skipped_non_food": 0,
            "errors": 0,
            "commodities": {},
        }

        print(f"\n{'='*70}")
        print("ROBIN HISTORICAL USDA_FOOD DATA IMPORT")
        print(f"Source: {self.data_path}")
        print(f"Files found: {len(files)}")
        print(f"{'='*70}\n")

        session = self.db_manager.get_session()
        batch = []

        try:
            for file_path in files:
                commodity_slug = self._extract_commodity_name(file_path)

                if commodity_slug in NON_FOOD_ITEMS:
                    stats["skipped_non_food"] += 1
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to parse {file_path.name}: {e}")
                    stats["errors"] += 1
                    continue

                commodity_name = data.get("commodity", commodity_slug)
                category = data.get("category", "Other")
                unit = data.get("unit", "lb")
                source = data.get("source", "USDA")

                historical = data.get("historicalData", [])
                if not historical:
                    continue

                file_imported = 0
                for obs in historical:
                    date_str = obs.get("date")
                    price = obs.get("price")
                    if not date_str or price is None:
                        continue

                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        continue

                    try:
                        price_float = float(price)
                    except (ValueError, TypeError):
                        continue

                    if price_float <= 0:
                        continue

                    batch.append({
                        "food_item": commodity_name,
                        "price": price_float,
                        "unit": unit,
                        "store_type": "Retail",
                        "location": "National Average",
                        "state": None,
                        "country": "USA",
                        "date": date_obj,
                        "source": source,
                        "brand": None,
                        "quality_grade": category,
                    })
                    stats["total_records"] += 1
                    file_imported += 1

                    if len(batch) >= batch_size:
                        result = self._insert_batch(session, batch)
                        stats["imported"] += result["inserted"]
                        stats["skipped"] += result["skipped"]
                        batch = []

                stats["commodities"][commodity_name] = file_imported
                if file_imported > 0:
                    print(
                        f"  {commodity_name}: {file_imported} daily records"
                    )

            if batch:
                result = self._insert_batch(session, batch)
                stats["imported"] += result["inserted"]
                stats["skipped"] += result["skipped"]

        finally:
            session.close()

        print(f"\n{'='*70}")
        print("HISTORICAL IMPORT COMPLETE")
        print(f"{'='*70}")
        print(f"Files processed: {stats['total_files']}")
        print(f"Non-food skipped: {stats['skipped_non_food']}")
        print(f"Commodities imported: {len(stats['commodities'])}")
        print(f"Total records: {stats['total_records']}")
        print(f"Imported: {stats['imported']}")
        print(f"Skipped (duplicates): {stats['skipped']}")
        print(f"Errors: {stats['errors']}")
        print()

        return stats

    def _extract_commodity_name(self, file_path: Path) -> str:
        """Extract commodity name from filename like '[2025.09.15] wheat.json'"""
        name = file_path.stem
        if "]" in name:
            name = name.split("]", 1)[1].strip()
        return name

    def _insert_batch(self, session, batch: List[Dict]) -> Dict:
        result = {"inserted": 0, "skipped": 0}

        for record_data in batch:
            existing = (
                session.query(RetailPrice)
                .filter(
                    RetailPrice.food_item == record_data["food_item"],
                    RetailPrice.date == record_data["date"],
                    RetailPrice.source == record_data["source"],
                )
                .first()
            )

            if existing:
                result["skipped"] += 1
                continue

            record = RetailPrice(**record_data)
            session.add(record)
            result["inserted"] += 1

        session.commit()
        return result


def main():
    print("Initializing Historical USDA Food Data Importer...")

    db_manager = DatabaseManager()
    db_manager.create_tables()

    importer = HistoricalImporter()
    importer.set_database_manager(db_manager)

    stats = importer.import_all()

    print(f"\nHistorical import complete!")
    print(f"Imported {stats['imported']} records across {len(stats['commodities'])} commodities")
    return stats


if __name__ == "__main__":
    main()
