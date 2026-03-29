"""
WASDE Data Importer
Loads USDA NASS WASDE data from Robin's canonical JSON files into SQLite database
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

from ..models import WASDEData
from ..manager import DatabaseManager

logger = logging.getLogger(__name__)


class WASDEImporter:
    """
    Import WASDE agricultural data from Robin's JSON files

    Handles:
    - Parsing 35 JSON files (189 MB)
    - Normalizing 101K+ data records
    - Converting price values to numeric
    - Bulk insert with progress tracking
    """

    def __init__(self, robin_data_path: Optional[str] = None):
        """
        Initialize WASDE importer

        Args:
            robin_data_path: Path to Robin's WASDE data directory.
                            Defaults to D:/Arcanum/Council/Robin/DATA/USDA_WASDE/
        """
        if robin_data_path is None:
            robin_data_path = "D:/Arcanum/Council/Robin/DATA/USDA_WASDE"

        self.robin_data_path = Path(robin_data_path)
        if not self.robin_data_path.exists():
            raise FileNotFoundError(
                f"Robin WASDE data directory not found: {robin_data_path}"
            )

        self.db_manager = None
        logger.info(f"WASDE Importer initialized: {robin_data_path}")

    def set_database_manager(self, db_manager: DatabaseManager):
        """Set the database manager to use for imports"""
        self.db_manager = db_manager

    def import_all_commodities(self, batch_size: int = 1000) -> Dict[str, int]:
        """
        Import all WASDE commodity data from Robin's JSON files

        Args:
            batch_size: Number of records to insert per batch

        Returns:
            Dictionary with import statistics
        """
        if not self.db_manager:
            raise ValueError("Database manager not set. Call set_database_manager() first.")

        # Find all WASDE JSON files
        json_files = list(self.robin_data_path.glob("wasde_*.json"))

        if not json_files:
            raise FileNotFoundError(f"No WASDE JSON files found in {self.robin_data_path}")

        stats = {
            'files_processed': 0,
            'total_records': 0,
            'price_records': 0,
            'errors': 0,
            'commodities': []
        }

        print(f"\n{'='*80}")
        print(f"WASDE DATA IMPORT")
        print(f"Files found: {len(json_files)}")
        print(f"{'='*80}\n")

        for json_file in sorted(json_files):
            try:
                commodity_stats = self.import_commodity_file(
                    json_file,
                    batch_size=batch_size
                )

                stats['files_processed'] += 1
                stats['total_records'] += commodity_stats['total_records']
                stats['price_records'] += commodity_stats['price_records']
                stats['commodities'].append(commodity_stats['commodity'])

                # Print progress
                print(f"[OK] {commodity_stats['commodity']:15s} - "
                      f"{commodity_stats['total_records']:6d} records "
                      f"({commodity_stats['price_records']:4d} prices)")

            except Exception as e:
                logger.error(f"Error importing {json_file.name}: {e}")
                stats['errors'] += 1
                print(f"[ERROR] {json_file.stem:15s} - Error: {str(e)[:50]}")

        print(f"\n{'='*80}")
        print(f"IMPORT COMPLETE")
        print(f"{'='*80}")
        print(f"Files processed: {stats['files_processed']}")
        print(f"Total records: {stats['total_records']:,}")
        print(f"Price records: {stats['price_records']:,}")
        print(f"Errors: {stats['errors']}")
        print(f"{'='*80}\n")

        # Update sync status
        self.db_manager.update_sync_status(
            source_name='WASDE',
            status='SUCCESS' if stats['errors'] == 0 else 'PARTIAL',
            records_synced=stats['total_records']
        )

        return stats

    def import_commodity_file(
        self,
        json_file: Path,
        batch_size: int = 1000
    ) -> Dict[str, int]:
        """
        Import a single WASDE commodity JSON file

        Args:
            json_file: Path to JSON file
            batch_size: Records per insert batch

        Returns:
            Dictionary with import statistics for this commodity
        """
        # Load JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        commodity = data.get('commodity', 'UNKNOWN')
        records = data.get('data', [])

        if not records:
            return {
                'commodity': commodity,
                'total_records': 0,
                'price_records': 0
            }

        # Parse and normalize records
        normalized_records = []
        price_count = 0

        for record in records:
            try:
                normalized = self._normalize_record(record, commodity)
                normalized_records.append(normalized)

                if 'PRICE' in normalized.statistic_category:
                    price_count += 1

            except Exception as e:
                logger.warning(f"Error normalizing record in {commodity}: {e}")
                continue

        # Bulk insert in batches
        session = self.db_manager.get_session()
        try:
            for i in range(0, len(normalized_records), batch_size):
                batch = normalized_records[i:i + batch_size]
                session.bulk_save_objects(batch)
                session.commit()
        finally:
            session.close()

        return {
            'commodity': commodity,
            'total_records': len(normalized_records),
            'price_records': price_count
        }

    def _normalize_record(self, record: Dict, commodity: str) -> WASDEData:
        """
        Normalize a single WASDE data record

        Args:
            record: Raw data record from JSON
            commodity: Commodity name

        Returns:
            WASDEData model instance
        """
        # Parse value and try to extract numeric value
        value_str = record.get('Value', '')
        numeric_value = self._extract_numeric_value(value_str)

        # Parse load_time
        load_time = None
        if record.get('load_time'):
            try:
                load_time = datetime.strptime(
                    record['load_time'],
                    '%Y-%m-%d %H:%M:%S.%f'
                )
            except ValueError:
                try:
                    load_time = datetime.strptime(
                        record['load_time'],
                        '%Y-%m-%d %H:%M:%S'
                    )
                except ValueError:
                    pass

        return WASDEData(
            commodity=commodity.upper(),
            statistic_category=record.get('statisticcat_desc', '').upper(),
            value=value_str,
            numeric_value=numeric_value,
            unit=record.get('unit_desc', ''),
            location=record.get('state_name', '').upper(),
            state_code=record.get('state_alpha', ''),
            agg_level=record.get('agg_level_desc', ''),
            year=int(record.get('year', 0)) if record.get('year') else None,
            reference_period=record.get('reference_period_desc', ''),
            short_desc=record.get('short_desc', ''),
            source_desc=record.get('source_desc', ''),
            sector=record.get('sector_desc', ''),
            group_desc=record.get('group_desc', ''),
            class_desc=record.get('class_desc', ''),
            freq_desc=record.get('freq_desc', ''),
            load_time=load_time,
            prodn_practice=record.get('prodn_practice_desc', ''),
            util_practice=record.get('util_practice_desc', ''),
            domain_desc=record.get('domain_desc', ''),
            domaincat_desc=record.get('domaincat_desc', '')
        )

    def _extract_numeric_value(self, value_str: str) -> Optional[float]:
        """
        Extract numeric value from WASDE value string

        Handles:
        - Simple numbers: "5.52" -> 5.52
        - Numbers with commas: "209,442,000" -> 209442000.0
        - Ranges: "5.50-6.00" -> 5.75 (midpoint)
        - Non-numeric values: "(D)" -> None

        Args:
            value_str: Value string from WASDE data

        Returns:
            Float value or None if not numeric
        """
        if not value_str or value_str == '(D)' or value_str == '(Z)':
            return None

        try:
            # Remove commas
            value_str = value_str.replace(',', '')

            # Check for range (e.g., "5.50-6.00")
            if '-' in value_str and not value_str.startswith('-'):
                parts = value_str.split('-')
                if len(parts) == 2:
                    try:
                        low = float(parts[0])
                        high = float(parts[1])
                        return (low + high) / 2  # Use midpoint
                    except ValueError:
                        pass

            # Try direct conversion
            return float(value_str)

        except (ValueError, AttributeError):
            return None

    def import_single_commodity(self, commodity: str) -> Dict[str, int]:
        """
        Import data for a single commodity

        Args:
            commodity: Commodity name (e.g., 'wheat', 'corn')

        Returns:
            Import statistics
        """
        json_file = self.robin_data_path / f"wasde_{commodity.lower()}_2025-10-23.json"

        if not json_file.exists():
            raise FileNotFoundError(f"WASDE file not found: {json_file}")

        return self.import_commodity_file(json_file)

    def verify_import(self) -> Dict[str, any]:
        """
        Verify imported data integrity

        Returns:
            Verification results
        """
        if not self.db_manager:
            raise ValueError("Database manager not set")

        stats = self.db_manager.get_database_stats()
        commodities = self.db_manager.get_wasde_commodities()

        # Get sample price data
        sample_prices = {}
        for commodity in commodities[:5]:  # Check first 5 commodities
            price_stats = self.db_manager.get_wasde_statistics(commodity)
            if price_stats:
                sample_prices[commodity] = price_stats

        return {
            'total_records': stats.get('wasde_data', 0),
            'commodities_imported': len(commodities),
            'commodities': commodities,
            'sample_prices': sample_prices
        }


# Command-line interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Import WASDE data from Robin into database')
    parser.add_argument('--data-path', help='Path to Robin WASDE data directory')
    parser.add_argument('--db-path', help='Path to SQLite database file')
    parser.add_argument('--commodity', help='Import single commodity only')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for inserts')

    args = parser.parse_args()

    # Initialize database manager
    db_manager = DatabaseManager(db_path=args.db_path)
    db_manager.create_tables()

    # Initialize importer
    importer = WASDEImporter(robin_data_path=args.data_path)
    importer.set_database_manager(db_manager)

    # Run import
    if args.commodity:
        print(f"Importing {args.commodity}...")
        stats = importer.import_single_commodity(args.commodity)
    else:
        print("Importing all WASDE commodities...")
        stats = importer.import_all_commodities(batch_size=args.batch_size)

    # Verify import
    print("\nVerifying import...")
    verification = importer.verify_import()
    print(f"Total records: {verification['total_records']:,}")
    print(f"Commodities: {verification['commodities_imported']}")
    print(f"Sample price data: {len(verification['sample_prices'])} commodities")

    print("\n[OK] Import complete!")
