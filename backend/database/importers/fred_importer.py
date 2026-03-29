"""
FRED Economic Data Importer
Loads FRED data from Robin's SQLite database into Foodberg database
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..models import EconomicIndicator
from ..manager import DatabaseManager

logger = logging.getLogger(__name__)


class FREDImporter:
    """
    Import FRED data from Robin's SQLite database

    Handles:
    - Reading from Robin's fred_data.db
    - Mapping FRED series to EconomicIndicator records
    - Bulk insert with progress tracking

    Key series for food price analysis:
    - GDP, GDPC1: Economic output
    - UNRATE: Unemployment (affects consumer demand)
    - CPIAUCSL: Consumer Price Index
    - CPILFESL: Core CPI (less food and energy)
    - PCEPI: PCE Price Index
    - FEDFUNDS: Fed funds rate (affects agricultural costs)
    """

    # Map FRED series IDs to categories
    SERIES_CATEGORIES = {
        "GDP": "Output",
        "GDPC1": "Output",
        "GDPPOT": "Output",
        "UNRATE": "Employment",
        "PAYEMS": "Employment",
        "CIVPART": "Employment",
        "CPIAUCSL": "Inflation",
        "CPILFESL": "Inflation",
        "PCEPI": "Inflation",
        "FEDFUNDS": "Interest Rates",
        "DGS10": "Interest Rates",
        "DGS2": "Interest Rates",
        "HOUST": "Housing",
        "RSAFS": "Retail",
        "INDPRO": "Production",
        "DCOILWTICO": "Energy",
        "DCOILBRENTEU": "Energy",
    }

    def __init__(self, robin_data_path: Optional[str] = None):
        """
        Initialize FRED importer

        Args:
            robin_data_path: Path to Robin's FRED database.
                            Defaults to D:/Arcanum/Council/Robin/DATA/FRED/fred_data/fred_data.db
        """
        if robin_data_path is None:
            robin_data_path = (
                "D:/Arcanum/Council/Robin/DATA/FRED/fred_data/fred_data.db"
            )

        self.robin_db_path = Path(robin_data_path)
        if not self.robin_db_path.exists():
            raise FileNotFoundError(f"Robin FRED database not found: {robin_data_path}")

        self.db_manager = None
        logger.info(f"FRED Importer initialized: {robin_data_path}")

    def set_database_manager(self, db_manager: DatabaseManager):
        """Set the database manager to use for imports"""
        self.db_manager = db_manager

    def import_all(self, batch_size: int = 500) -> Dict[str, int]:
        """
        Import all FRED data

        Args:
            batch_size: Number of records to insert per batch

        Returns:
            Dictionary with import statistics
        """
        if not self.db_manager:
            raise ValueError(
                "Database manager not set. Call set_database_manager() first."
            )

        stats = {
            "source": str(self.robin_db_path.name),
            "total_records": 0,
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "series": {},
        }

        print(f"\n{'='*80}")
        print(f"FRED ECONOMIC DATA IMPORT")
        print(f"Source: {self.robin_db_path.name}")
        print(f"{'='*80}\n")

        try:
            # Connect to Robin's FRED database
            robin_conn = sqlite3.connect(str(self.robin_db_path))
            robin_cursor = robin_conn.cursor()

            # Get all series with their metadata
            robin_cursor.execute(
                """
                SELECT series_id, title, frequency, units
                FROM fred_series
            """
            )
            series_info = {
                row[0]: {"title": row[1], "frequency": row[2], "units": row[3]}
                for row in robin_cursor.fetchall()
            }

            print(f"Found {len(series_info)} series")

            # Get all observations
            robin_cursor.execute(
                """
                SELECT series_id, date, value
                FROM fred_observations
                ORDER BY series_id, date
            """
            )

            batch = []
            for row in robin_cursor.fetchall():
                series_id, date_str, value = row

                # Get series metadata
                meta = series_info.get(series_id, {})

                converted = self._convert_to_indicator(series_id, date_str, value, meta)
                if converted:
                    batch.append(converted)
                    stats["total_records"] += 1

                    # Track by series
                    if series_id not in stats["series"]:
                        stats["series"][series_id] = 0
                    stats["series"][series_id] += 1

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

            robin_conn.close()

            # Print series summary
            print("\nSeries breakdown:")
            for series_id, count in sorted(stats["series"].items()):
                meta = series_info.get(series_id, {})
                title = meta.get("title", series_id)[:50]
                print(f"  {series_id}: {count} records - {title}")

            print(f"\n{'='*80}")
            print(f"FRED IMPORT COMPLETE")
            print(f"{'='*80}")
            print(f"Total records: {stats['total_records']}")
            print(f"Imported: {stats['imported']}")
            print(f"Skipped (duplicates): {stats['skipped']}")
            print(f"Errors: {stats['errors']}")
            print()

        except Exception as e:
            logger.error(f"FRED import failed: {e}")
            stats["errors"] += 1
            import traceback

            traceback.print_exc()

        return stats

    def _convert_to_indicator(
        self, series_id: str, date_str: str, value: float, meta: Dict
    ) -> Optional[Dict]:
        """
        Convert FRED observation to EconomicIndicator model format
        """
        if not series_id or not date_str or value is None:
            return None

        # Parse date
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}")
            return None

        # Get category
        category = self.SERIES_CATEGORIES.get(series_id, "Other")

        # Get indicator name
        indicator_name = meta.get("title", series_id)

        # Get frequency
        frequency = meta.get("frequency", "Monthly")
        # Normalize frequency
        freq_map = {
            "Monthly": "Monthly",
            "Quarterly": "Quarterly",
            "Annual": "Annual",
            "Daily": "Daily",
            "Weekly": "Weekly",
        }
        frequency = freq_map.get(frequency, "Monthly")

        return {
            "date": date_obj,
            "series_id": series_id,
            "indicator_name": indicator_name,
            "value": float(value),
            "category": category,
            "frequency": frequency,
            "source": "FRED",
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
                        EconomicIndicator.source == record_data["source"],
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
    """CLI for FRED data import"""
    from ..manager import DatabaseManager

    print("Initializing FRED importer...")

    db_manager = DatabaseManager()
    importer = FREDImporter()
    importer.set_database_manager(db_manager)

    stats = importer.import_all()

    print("\n✅ FRED import complete!")
    return stats


if __name__ == "__main__":
    main()
