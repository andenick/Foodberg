"""
Database Migration Script
One-time setup to create tables and import initial data
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.manager import DatabaseManager
from database.importers.wasde_importer import WASDEImporter
from database.importers.live_sync import LiveDataSync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Run database migration

    Steps:
    1. Create all tables
    2. Import WASDE data from Robin
    3. Sync live data sources (USDA Market News, FRED)
    4. Verify data integrity
    5. Generate summary report
    """
    print("\n" + "="*80)
    print("FOODBERG DATABASE MIGRATION")
    print("="*80 + "\n")

    start_time = datetime.now()

    # Initialize database manager
    print("[1/5] Initializing database...")
    db_path = str(Path(__file__).parent.parent / 'data' / 'foodberg.db')
    db_manager = DatabaseManager(db_path=db_path)

    # Create tables
    print("[2/5] Creating database tables...")
    db_manager.create_tables()
    print("[OK] Tables created successfully\n")

    # Import WASDE data
    print("[3/5] Importing WASDE data from Robin...")
    wasde_importer = WASDEImporter()
    wasde_importer.set_database_manager(db_manager)

    try:
        wasde_stats = wasde_importer.import_all_commodities(batch_size=1000)
        print(f"[OK] WASDE import complete: {wasde_stats['total_records']:,} records\n")
    except Exception as e:
        logger.error(f"Error importing WASDE data: {e}")
        print(f"[ERROR] WASDE import failed: {e}\n")
        wasde_stats = {'total_records': 0}

    # Sync live data sources
    print("[4/5] Syncing live data sources...")
    sync = LiveDataSync(db_manager)

    try:
        sync_results = asyncio.run(sync.sync_all_sources())

        for source, result in sync_results.items():
            status = result.get('status', 'UNKNOWN')
            records = result.get('records_synced', 0)
            if status in ['SUCCESS', 'PARTIAL']:
                print(f"[OK] {source}: {records:,} records")
            elif status == 'NOT_IMPLEMENTED':
                print(f"[INFO] {source}: Not implemented yet")
            else:
                print(f"[ERROR] {source}: {result.get('error', 'Failed')}")

        print()
    except Exception as e:
        logger.error(f"Error syncing live data: {e}")
        print(f"[ERROR] Live data sync failed: {e}\n")
        sync_results = {}

    # Verify data integrity
    print("[5/5] Verifying data integrity...")
    stats = db_manager.get_database_stats()

    print(f"\nDatabase Statistics:")
    print(f"  WASDE Data:           {stats.get('wasde_data', 0):8,} records")
    print(f"  Market Prices:        {stats.get('market_prices', 0):8,} records")
    print(f"  Economic Indicators:  {stats.get('economic_indicators', 0):8,} records")
    print(f"  Global Prices:        {stats.get('global_prices', 0):8,} records")
    print(f"  Retail Prices:        {stats.get('retail_prices', 0):8,} records")
    print(f"  {'-'*40}")
    print(f"  Total:                {stats.get('total', 0):8,} records")

    # Get WASDE verification
    verification = wasde_importer.verify_import()
    print(f"\nWASDE Verification:")
    print(f"  Commodities: {verification['commodities_imported']}")
    print(f"  Sample commodities: {', '.join(verification['commodities'][:5])}")

    # Completion time
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{'='*80}")
    print(f"MIGRATION COMPLETE")
    print(f"{'='*80}")
    print(f"Duration: {duration:.1f} seconds")
    print(f"Database: {db_path}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
