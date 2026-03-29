#!/usr/bin/env python3
"""
Comprehensive WASDE Data Import
Imports all 35 commodities from Robin's JSON files
Target: 1-2M+ records across 188MB of data
"""

import json
import time
from datetime import datetime
from pathlib import Path
import logging

from database.manager import DatabaseManager
from database.models import WASDEData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComprehensiveWASDEImporter:
    """
    Import all 35 WASDE commodities from Robin's DATA directory
    """

    def __init__(self, robin_data_path="D:/Arcanum/Council/Robin/DATA/USDA_WASDE"):
        self.robin_data_path = Path(robin_data_path)
        if not self.robin_data_path.exists():
            raise FileNotFoundError(f"Robin WASDE data directory not found: {robin_data_path}")
        self.db_manager = DatabaseManager()

    def get_available_commodity_files(self):
        """Find all WASDE JSON files in Robin's directory"""
        files = list(self.robin_data_path.glob("wasde_*.json"))
        commodities = []

        for file_path in sorted(files):
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            # Extract commodity name from filename
            commodity_name = file_path.stem.split('_')[1]  # wasde_wheat_2025-10-23.json -> wheat

            commodities.append({
                'commodity': commodity_name,
                'filename': file_path.name,
                'file_path': file_path,
                'file_size_mb': round(file_size_mb, 2)
            })

        return commodities

    def load_commodity_data(self, file_path):
        """Load data for a specific commodity from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return None

    def _extract_numeric_value(self, value_str):
        """Extract numeric value from string, handling ranges and special values"""
        if not value_str or value_str in ['(D)', '(S)', '(NA)', '', 'None']:
            return None

        # Remove commas
        value_str = str(value_str).replace(',', '').strip()

        # Handle ranges (take midpoint)
        if '-' in value_str and not value_str.startswith('-'):
            parts = value_str.split('-')
            try:
                return (float(parts[0]) + float(parts[1])) / 2
            except:
                return None

        # Try to convert to float
        try:
            return float(value_str)
        except:
            return None

    def import_commodity(self, commodity_info, batch_size=1000):
        """Import data for one commodity"""
        commodity_name = commodity_info['commodity']

        print(f"\nImporting {commodity_name.upper()}...")
        print(f"  File: {commodity_info['filename']}")
        print(f"  Size: {commodity_info['file_size_mb']} MB")

        # Load data from file
        data = self.load_commodity_data(commodity_info['file_path'])
        if not data:
            print(f"  [ERROR] Failed to load {commodity_name}")
            return 0

        # Handle both dict and list formats
        if isinstance(data, dict):
            records = data.get('data', [])
        elif isinstance(data, list):
            records = data
        else:
            print(f"  [ERROR] Unexpected data format for {commodity_name}")
            return 0

        total_records = len(records)
        price_records = 0

        print(f"  Records to import: {total_records:,}")

        # Process in batches
        session = self.db_manager.get_session()
        batch = []
        imported = 0

        try:
            for idx, record in enumerate(records):
                # Extract numeric value (JSON field is 'Value' with capital V)
                numeric_value = self._extract_numeric_value(record.get('Value', record.get('value')))
                if numeric_value is not None:
                    price_records += 1

                # Parse load_time from string to datetime
                load_time = None
                if record.get('load_time'):
                    try:
                        load_time = datetime.strptime(record.get('load_time'), '%Y-%m-%d %H:%M:%S.%f')
                    except:
                        pass

                # Create WASDEData object with correct field mapping
                wasde_record = WASDEData(
                    commodity=record.get('commodity_desc', commodity_name).upper(),
                    statistic_category=record.get('statisticcat_desc', ''),
                    value=record.get('Value', record.get('value')),  # Note: JSON has capital 'V'
                    numeric_value=numeric_value,
                    unit=record.get('unit_desc', ''),
                    location=record.get('location_desc', record.get('state_name', 'Unknown')),
                    state_code=record.get('state_alpha', ''),
                    agg_level=record.get('agg_level_desc', ''),
                    year=record.get('year'),
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
                    domaincat_desc=record.get('domaincat_desc', ''),
                    imported_at=datetime.now()
                )

                batch.append(wasde_record)

                # Insert batch when full
                if len(batch) >= batch_size:
                    session.bulk_save_objects(batch)
                    session.commit()
                    imported += len(batch)

                    # Progress indicator
                    progress = (idx + 1) / total_records * 100
                    print(f"  Progress: {progress:.1f}% ({imported:,}/{total_records:,})", end='\r')

                    batch = []

            # Insert remaining records
            if batch:
                session.bulk_save_objects(batch)
                session.commit()
                imported += len(batch)

            print(f"\n  [OK] Imported {imported:,} records ({price_records:,} with prices)")

            # Update sync status
            self.db_manager.update_sync_status(
                source_name=f'WASDE-{commodity_name.upper()}',
                status='SUCCESS',
                records_synced=imported
            )

            return imported

        except Exception as e:
            session.rollback()
            print(f"\n  [ERROR] Failed to import {commodity_name}: {e}")
            logger.exception(e)

            # Update sync status
            self.db_manager.update_sync_status(
                source_name=f'WASDE-{commodity_name.upper()}',
                status='FAILED',
                error_message=str(e)
            )

            return 0
        finally:
            session.close()

    def import_all(self):
        """Import all available commodities"""
        print("\n" + "="*80)
        print("COMPREHENSIVE WASDE DATA IMPORT")
        print("Source: Robin Council Tool - D:/Arcanum/Council/Robin/DATA/USDA_WASDE")
        print("="*80)

        # Get commodity files
        commodities = self.get_available_commodity_files()
        if not commodities:
            print("ERROR: No WASDE JSON files found!")
            return

        print(f"\nFound {len(commodities)} commodities to import")
        print(f"Total size: {sum(c['file_size_mb'] for c in commodities):.2f} MB")
        print(f"Target: 1-2M+ total records\n")

        # Import each commodity
        start_time = time.time()
        total_imported = 0
        successful = 0
        failed = []

        for idx, commodity_info in enumerate(commodities, 1):
            print(f"\n[{idx}/{len(commodities)}] ", end='')

            count = self.import_commodity(commodity_info)
            total_imported += count

            if count > 0:
                successful += 1
            else:
                failed.append(commodity_info['commodity'])

        # Summary
        duration = time.time() - start_time

        print("\n" + "="*80)
        print("IMPORT COMPLETE")
        print("="*80)
        print(f"Commodities processed: {len(commodities)}")
        print(f"Successful imports:    {successful}")
        print(f"Failed imports:        {len(failed)}")
        print(f"Total records:         {total_imported:,}")
        print(f"Duration:              {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"Records/second:        {total_imported/duration:,.0f}")

        if failed:
            print(f"\nFailed commodities: {', '.join(failed)}")

        # Database size estimate
        print(f"\nEstimated database size: {(total_imported * 2 / 1024):.0f} MB")
        print("="*80)


def main():
    """Run comprehensive import"""
    importer = ComprehensiveWASDEImporter()
    importer.import_all()


if __name__ == '__main__':
    main()
