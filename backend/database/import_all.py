"""
Master Import Script for Foodberg
Runs all data importers in sequence, populating the SQLite database
from Robin's canonical data stores and local Inputs/ files.

Usage:
    cd backend
    python -m database.import_all
"""

import sys
from pathlib import Path
from datetime import datetime

# Ensure backend is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.manager import DatabaseManager
from database.models import Base, DataSourceSync


def run_all_imports():
    print("=" * 80)
    print("FOODBERG MASTER DATA IMPORT")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 80)

    # Initialize database
    db_manager = DatabaseManager()
    print("Database initialized.\n")

    all_stats = {}

    # 1. FRED Economic Indicators
    print("\n[1/5] FRED Economic Indicators...")
    try:
        from database.importers.fred_importer import FREDImporter
        importer = FREDImporter()
        importer.set_database_manager(db_manager)
        stats = importer.import_all()
        all_stats["FRED"] = stats
        _update_sync(db_manager, "FRED", stats)
    except Exception as e:
        print(f"  FRED import failed: {e}")
        all_stats["FRED"] = {"error": str(e)}

    # 2. BLS CPI Food Data
    print("\n[2/5] BLS CPI Food Data...")
    try:
        from database.importers.bls_importer import BLSImporter
        importer = BLSImporter()
        importer.set_database_manager(db_manager)
        stats = importer.import_all()
        all_stats["BLS"] = stats
        _update_sync(db_manager, "BLS", stats)
    except Exception as e:
        print(f"  BLS import failed: {e}")
        all_stats["BLS"] = {"error": str(e)}

    # 3. FAO Food Price Index
    print("\n[3/5] FAO Food Price Index...")
    try:
        from database.importers.fao_importer import FAOImporter
        importer = FAOImporter()
        importer.set_database_manager(db_manager)
        stats = importer.import_all()
        all_stats["FAO"] = stats
        _update_sync(db_manager, "FAO", stats)
    except Exception as e:
        print(f"  FAO import failed: {e}")
        all_stats["FAO"] = {"error": str(e)}

    # 4. World Bank Commodity Data
    print("\n[4/5] World Bank WDI Data...")
    try:
        from database.importers.worldbank_importer import WorldBankImporter
        importer = WorldBankImporter()
        importer.set_database_manager(db_manager)
        stats = importer.import_all()
        all_stats["World Bank"] = stats
        _update_sync(db_manager, "World Bank", stats)
    except Exception as e:
        print(f"  World Bank import failed: {e}")
        all_stats["World Bank"] = {"error": str(e)}

    # 5. Inputs/ Retail Price Data
    print("\n[5/5] Inputs/ Retail Prices...")
    try:
        from database.importers.inputs_importer import InputsImporter
        importer = InputsImporter()
        importer.set_database_manager(db_manager)
        stats = importer.import_all()
        all_stats["Inputs"] = stats
        _update_sync(db_manager, "Inputs", stats)
    except Exception as e:
        print(f"  Inputs import failed: {e}")
        all_stats["Inputs"] = {"error": str(e)}

    # Final summary
    print("\n" + "=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)

    for source, stats in all_stats.items():
        if "error" in stats:
            print(f"  {source}: FAILED - {stats['error']}")
        else:
            imported = stats.get("imported", 0)
            skipped = stats.get("skipped", 0)
            total = stats.get("total_records", 0)
            print(f"  {source}: {imported} imported, {skipped} skipped (of {total} total)")

    # Print database table counts
    print("\nDatabase table counts:")
    try:
        db_stats = db_manager.get_database_stats()
        for table, count in db_stats.items():
            print(f"  {table}: {count} records")
    except Exception as e:
        print(f"  Could not get stats: {e}")

    print(f"\nCompleted: {datetime.now().isoformat()}")
    print("=" * 80)

    return all_stats


def _update_sync(db_manager, source_name: str, stats: dict):
    """Update the data_source_sync table after an import"""
    try:
        imported = stats.get("imported", 0)
        status = "SUCCESS" if imported > 0 else "NO_DATA"
        db_manager.update_sync_status(
            source_name=source_name,
            status=status,
            records_synced=imported,
        )
    except Exception:
        pass


if __name__ == "__main__":
    run_all_imports()
