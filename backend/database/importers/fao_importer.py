"""
FAO Food Price Index Importer
Loads FAO data from Robin's JSON files into SQLite database GlobalPrice table
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..models import GlobalPrice
from ..manager import DatabaseManager

logger = logging.getLogger(__name__)


class FAOImporter:
    """
    Import FAO Food Price Index data from Robin's JSON files

    Handles:
    - Parsing FAO Food Price Index JSON
    - Converting monthly data to GlobalPrice records
    - Bulk insert with progress tracking

    Indices available:
    - Food Price Index (overall)
    - Meat
    - Dairy
    - Cereals
    - Oils
    - Sugar
    """

    def __init__(self, robin_data_path: Optional[str] = None):
        """
        Initialize FAO importer

        Args:
            robin_data_path: Path to Robin's FAO data directory.
                            Defaults to D:/Arcanum/Council/Robin/DATA/FAO/
        """
        if robin_data_path is None:
            robin_data_path = "D:/Arcanum/Council/Robin/DATA/FAO"

        self.robin_data_path = Path(robin_data_path)
        if not self.robin_data_path.exists():
            raise FileNotFoundError(
                f"Robin FAO data directory not found: {robin_data_path}"
            )

        self.db_manager = None
        logger.info(f"FAO Importer initialized: {robin_data_path}")

    def set_database_manager(self, db_manager: DatabaseManager):
        """Set the database manager to use for imports"""
        self.db_manager = db_manager

    def find_latest_json(self) -> Path:
        """Find the most recent FAO JSON file"""
        json_files = list(self.robin_data_path.glob("fao_food_price_index_*.json"))
        if not json_files:
            raise FileNotFoundError(
                f"No FAO JSON files found in {self.robin_data_path}"
            )

        # Sort by date in filename and get latest
        return sorted(json_files)[-1]

    def import_all(self, batch_size: int = 500) -> Dict[str, int]:
        """
        Import all FAO Food Price Index data

        Args:
            batch_size: Number of records to insert per batch

        Returns:
            Dictionary with import statistics
        """
        if not self.db_manager:
            raise ValueError(
                "Database manager not set. Call set_database_manager() first."
            )

        json_file = self.find_latest_json()

        stats = {
            "file": str(json_file.name),
            "total_records": 0,
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "indices": {},
        }

        print(f"\n{'='*80}")
        print(f"FAO FOOD PRICE INDEX IMPORT")
        print(f"Source: {json_file.name}")
        print(f"{'='*80}\n")

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # FAO JSON structure: categories -> {food, meat, dairy, cereals, oils, sugar}
            categories = data.get("categories", {})
            retrieved_at = data.get("retrieved_at", "unknown")

            print(f"Data retrieved: {retrieved_at}")
            print(f"Categories: {list(categories.keys())}")
            print()

            # Map category names to price_ids
            category_mapping = {
                "food": "fao_food_overall",
                "meat": "fao_food_meat",
                "dairy": "fao_food_dairy",
                "cereals": "fao_food_cereals",
                "oils": "fao_food_oils",
                "sugar": "fao_food_sugar",
            }

            # Process each category
            batch = []
            for cat_name, records in categories.items():
                price_id = category_mapping.get(cat_name)
                if not price_id:
                    logger.warning(f"Unknown category: {cat_name}")
                    continue

                stats["indices"][cat_name] = len(records)

                for record in records:
                    converted = self._convert_category_record(
                        record, price_id, cat_name
                    )
                    if converted:
                        batch.append(converted)
                        stats["total_records"] += 1

                    # Insert batch
                    if len(batch) >= batch_size:
                        result = self._insert_batch(batch)
                        stats["imported"] += result["inserted"]
                        stats["skipped"] += result["skipped"]
                        batch = []

                print(f"  {cat_name}: {len(records)} records")

            # Insert remaining
            if batch:
                result = self._insert_batch(batch)
                stats["imported"] += result["inserted"]
                stats["skipped"] += result["skipped"]

            print(f"\n{'='*80}")
            print(f"FAO IMPORT COMPLETE")
            print(f"{'='*80}")
            print(f"Total records: {stats['total_records']}")
            print(f"Imported: {stats['imported']}")
            print(f"Skipped (duplicates): {stats['skipped']}")
            print(f"Errors: {stats['errors']}")
            print()

        except Exception as e:
            logger.error(f"FAO import failed: {e}")
            stats["errors"] += 1
            import traceback

            traceback.print_exc()

        return stats

    def _convert_category_record(
        self, record: Dict, price_id: str, category: str
    ) -> Optional[Dict]:
        """
        Convert a FAO category record to GlobalPrice model format

        Args:
            record: FAO record with date, value, index_type
            price_id: The price_id to use (e.g., 'fao_food_overall')
            category: The category name (e.g., 'food')
        """
        date_str = record.get("date", "")
        if not date_str:
            return None

        value = record.get("value")
        if value is None:
            return None

        # Convert YYYY-MM to datetime
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m")
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}")
            return None

        # Map to GlobalPrice model fields
        # commodity: Use category name (e.g., "FAO Food Price Index - Overall")
        # price: The index value
        # unit: "index" (base 2014-2016=100)
        # region: "Global"
        # source: "FAO"
        # indicator_code: The internal price_id

        return {
            "date": date_obj,
            "commodity": f"FAO Food Price Index - {category.title()}",
            "price": float(value),
            "currency": "index",  # Not a real currency, it's an index value
            "unit": "2014-2016=100",
            "region": "Global",
            "country": None,
            "source": "FAO",
            "indicator_code": price_id,
        }

    def _insert_batch(self, batch: List[Dict]) -> Dict[str, int]:
        """Insert a batch of GlobalPrice records"""
        result = {"inserted": 0, "skipped": 0}

        with self.db_manager.get_session() as session:
            for record_data in batch:
                # Check for existing record (by date + commodity + source)
                existing = (
                    session.query(GlobalPrice)
                    .filter(
                        GlobalPrice.date == record_data["date"],
                        GlobalPrice.commodity == record_data["commodity"],
                        GlobalPrice.source == record_data["source"],
                    )
                    .first()
                )

                if existing:
                    result["skipped"] += 1
                    continue

                # Create new record
                record = GlobalPrice(
                    date=record_data["date"],
                    commodity=record_data["commodity"],
                    price=record_data["price"],
                    currency=record_data["currency"],
                    unit=record_data["unit"],
                    region=record_data["region"],
                    country=record_data["country"],
                    source=record_data["source"],
                    indicator_code=record_data["indicator_code"],
                )
                session.add(record)
                result["inserted"] += 1

            session.commit()

        return result


def main():
    """CLI for FAO data import"""
    from ..manager import DatabaseManager

    print("Initializing FAO importer...")

    db_manager = DatabaseManager()
    importer = FAOImporter()
    importer.set_database_manager(db_manager)

    stats = importer.import_all()

    print("\n✅ FAO import complete!")
    return stats


if __name__ == "__main__":
    main()
