"""
BLS Food CPI Importer
Loads BLS Consumer Price Index data from Robin's CSV files into SQLite database
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..models import EconomicIndicator
from ..manager import DatabaseManager

logger = logging.getLogger(__name__)


class BLSImporter:
    """
    Import BLS CPI data from Robin's CSV files

    Handles:
    - Parsing BLS data CSV files
    - Mapping CPI series to categories
    - Bulk insert with progress tracking

    Series imported:
    - CUUR0000SAF: Food and beverages
    - CUUR0000SAF11: Food at home
    - CUUR0000SEFV: Food away from home
    - CUUR0000SAF111: Cereals and bakery
    - CUUR0000SAF112: Meats, poultry, fish, eggs
    - CUUR0000SEFJ: Dairy
    - CUUR0000SAF113: Fruits and vegetables
    """

    # Map BLS series IDs to human-readable names
    SERIES_NAMES = {
        "CUUR0000SAF": "CPI - Food and Beverages",
        "CUUR0000SAF11": "CPI - Food at Home",
        "CUUR0000SEFV": "CPI - Food Away from Home",
        "CUUR0000SAF111": "CPI - Cereals and Bakery",
        "CUUR0000SAF112": "CPI - Meats, Poultry, Fish, Eggs",
        "CUUR0000SEFJ": "CPI - Dairy",
        "CUUR0000SAF113": "CPI - Fruits and Vegetables",
        "CUUR0000SA0": "CPI - All Items",
        "CUUR0000SA0L1E": "CPI - All Items Less Food and Energy",
        "CUUR0000SAE": "CPI - Energy",
    }

    def __init__(self, robin_data_path: Optional[str] = None):
        """
        Initialize BLS importer

        Args:
            robin_data_path: Path to Robin's BLS data directory.
                            Defaults to D:/Arcanum/Council/Robin/API_MODULES/BLS/data/
        """
        if robin_data_path is None:
            robin_data_path = "D:/Arcanum/Council/Robin/API_MODULES/BLS/data"

        self.robin_data_path = Path(robin_data_path)
        if not self.robin_data_path.exists():
            raise FileNotFoundError(
                f"Robin BLS data directory not found: {robin_data_path}"
            )

        self.db_manager = None
        logger.info(f"BLS Importer initialized: {robin_data_path}")

    def set_database_manager(self, db_manager: DatabaseManager):
        """Set the database manager to use for imports"""
        self.db_manager = db_manager

    def find_latest_csv(self) -> Path:
        """Find the most recent BLS CSV file"""
        csv_files = list(self.robin_data_path.glob("bls_data_*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No BLS CSV files found in {self.robin_data_path}")

        # Sort by name (date in filename) and get latest
        return sorted(csv_files)[-1]

    def import_all(self, batch_size: int = 500) -> Dict[str, int]:
        """
        Import all BLS CPI data

        Args:
            batch_size: Number of records to insert per batch

        Returns:
            Dictionary with import statistics
        """
        if not self.db_manager:
            raise ValueError(
                "Database manager not set. Call set_database_manager() first."
            )

        csv_file = self.find_latest_csv()

        stats = {
            "file": str(csv_file.name),
            "total_records": 0,
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "series": {},
        }

        print(f"\n{'='*80}")
        print(f"BLS CONSUMER PRICE INDEX IMPORT")
        print(f"Source: {csv_file.name}")
        print(f"{'='*80}\n")

        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                batch = []
                for row in reader:
                    converted = self._convert_to_indicator(row)
                    if converted:
                        batch.append(converted)
                        stats["total_records"] += 1

                        # Track by series
                        series = row.get("series_id", "unknown")
                        if series not in stats["series"]:
                            stats["series"][series] = 0
                        stats["series"][series] += 1

                    # Insert batch
                    if len(batch) >= batch_size:
                        result = self._insert_batch(batch)
                        stats["imported"] += result["inserted"]
                        stats["skipped"] += result["skipped"]
                        batch = []

                # Insert remaining
                if batch:
                    result = self._insert_batch(batch)
                    stats["imported"] += result["inserted"]
                    stats["skipped"] += result["skipped"]

            # Print series summary
            print("Series breakdown:")
            for series_id, count in sorted(stats["series"].items()):
                name = self.SERIES_NAMES.get(series_id, series_id)
                print(f"  {name}: {count} records")

            print(f"\n{'='*80}")
            print(f"BLS IMPORT COMPLETE")
            print(f"{'='*80}")
            print(f"Total records: {stats['total_records']}")
            print(f"Imported: {stats['imported']}")
            print(f"Skipped (duplicates): {stats['skipped']}")
            print(f"Errors: {stats['errors']}")
            print()

        except Exception as e:
            logger.error(f"BLS import failed: {e}")
            stats["errors"] += 1
            import traceback

            traceback.print_exc()

        return stats

    def _convert_to_indicator(self, row: Dict) -> Optional[Dict]:
        """
        Convert BLS CSV row to EconomicIndicator model format
        """
        series_id = row.get("series_id", "")
        date_str = row.get("date", "")
        value_str = row.get("value", "")

        if not series_id or not date_str or not value_str:
            return None

        # Parse date
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}")
            return None

        # Parse value
        try:
            value = float(value_str)
        except ValueError:
            logger.warning(f"Invalid value: {value_str}")
            return None

        # Get human-readable name
        indicator_name = self.SERIES_NAMES.get(series_id, series_id)

        # Determine category based on series
        if "SA" in series_id and "F" in series_id:
            category = "Food CPI"
        elif "SAE" in series_id:
            category = "Energy CPI"
        else:
            category = "CPI"

        return {
            "date": date_obj,
            "series_id": series_id,
            "indicator_name": indicator_name,
            "value": value,
            "category": category,
            "frequency": "Monthly",
            "source": "BLS",
        }

    def _insert_batch(self, batch: List[Dict]) -> Dict[str, int]:
        """Insert a batch of EconomicIndicator records"""
        result = {"inserted": 0, "skipped": 0}

        with self.db_manager.get_session() as session:
            for record_data in batch:
                # Check for existing record
                existing = (
                    session.query(EconomicIndicator)
                    .filter(
                        EconomicIndicator.date == record_data["date"],
                        EconomicIndicator.series_id == record_data["series_id"],
                    )
                    .first()
                )

                if existing:
                    result["skipped"] += 1
                    continue

                # Create new record
                record = EconomicIndicator(
                    date=record_data["date"],
                    series_id=record_data["series_id"],
                    indicator_name=record_data["indicator_name"],
                    value=record_data["value"],
                    category=record_data["category"],
                    frequency=record_data["frequency"],
                    source=record_data["source"],
                )
                session.add(record)
                result["inserted"] += 1

            session.commit()

        return result


def main():
    """CLI for BLS data import"""
    from ..manager import DatabaseManager

    print("Initializing BLS importer...")

    db_manager = DatabaseManager()
    importer = BLSImporter()
    importer.set_database_manager(db_manager)

    stats = importer.import_all()

    print("\n✅ BLS import complete!")
    return stats


if __name__ == "__main__":
    main()
