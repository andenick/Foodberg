#!/usr/bin/env python3
"""
Foodberg Data Pipeline
Collect data from APIs and import into database

Usage:
    python data_pipeline.py collect              # Collect from APIs
    python data_pipeline.py import               # Import collected data to DB
    python data_pipeline.py collect-and-import   # Both steps
    python data_pipeline.py status               # Show database status
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def collect_data():
    """Collect data from all API sources"""
    from data_sources.collectors import collect_all_data

    print("\n" + "#" * 60)
    print("# FOODBERG DATA COLLECTION")
    print("# Fetching from FRED, BLS, FAO APIs")
    print("#" * 60)

    results = collect_all_data()

    print("\n" + "=" * 60)
    print("COLLECTION SUMMARY")
    print("=" * 60)

    success = 0
    for source, info in results["sources"].items():
        status = info.get("status", "unknown")
        if status == "success":
            obs = info.get("observations", 0)
            print(f"  ✓ {source.upper()}: {obs:,} observations")
            success += 1
        else:
            print(f"  ✗ {source.upper()}: {info.get('error', 'failed')}")

    print(f"\nSuccessful: {success}/{len(results['sources'])}")
    return results


def import_data():
    """Import collected data into database"""
    from database.manager import DatabaseManager
    from database.importers.standalone_importers import (
        StandaloneFAOImporter,
        StandaloneFREDImporter,
        StandaloneBLSImporter,
    )

    print("\n" + "#" * 60)
    print("# FOODBERG DATABASE IMPORT")
    print("# Loading collected data into SQLite")
    print("#" * 60)

    db = DatabaseManager()
    results = {}

    # FAO
    print("\n[1/3] Importing FAO data...")
    try:
        importer = StandaloneFAOImporter()
        importer.set_database_manager(db)
        results["fao"] = importer.import_all()
    except Exception as e:
        print(f"  ✗ FAO import failed: {e}")
        results["fao"] = {"error": str(e)}

    # FRED
    print("\n[2/3] Importing FRED data...")
    try:
        importer = StandaloneFREDImporter()
        importer.set_database_manager(db)
        results["fred"] = importer.import_all()
    except Exception as e:
        print(f"  ✗ FRED import failed: {e}")
        results["fred"] = {"error": str(e)}

    # BLS
    print("\n[3/3] Importing BLS data...")
    try:
        importer = StandaloneBLSImporter()
        importer.set_database_manager(db)
        results["bls"] = importer.import_all()
    except Exception as e:
        print(f"  ✗ BLS import failed: {e}")
        results["bls"] = {"error": str(e)}

    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)

    for source, info in results.items():
        if "error" in info:
            print(f"  ✗ {source.upper()}: {info['error']}")
        else:
            print(f"  ✓ {source.upper()}: {info.get('imported', 0):,} imported")

    return results


def show_status():
    """Show database status"""
    from database.manager import DatabaseManager
    from database.models import WASDEData, EconomicIndicator, GlobalPrice
    from sqlalchemy import func

    db = DatabaseManager()

    print("\n" + "=" * 60)
    print("FOODBERG DATABASE STATUS")
    print("=" * 60)

    with db.get_session() as session:
        wasde = session.query(WASDEData).count()
        indicators = session.query(EconomicIndicator).count()
        global_prices = session.query(GlobalPrice).count()

        print(f"\nTable Counts:")
        print(f"  WASDE Data:          {wasde:,} records")
        print(f"  Economic Indicators: {indicators:,} records")
        print(f"  Global Prices:       {global_prices:,} records")

        # Source breakdown
        print(f"\nEconomic Indicator Sources:")
        sources = (
            session.query(EconomicIndicator.source, func.count(EconomicIndicator.id))
            .group_by(EconomicIndicator.source)
            .all()
        )
        for source, count in sources:
            print(f"  {source}: {count:,}")

        print(f"\nGlobal Price Sources:")
        sources = (
            session.query(GlobalPrice.source, func.count(GlobalPrice.id))
            .group_by(GlobalPrice.source)
            .all()
        )
        for source, count in sources:
            print(f"  {source}: {count:,}")

        total = wasde + indicators + global_prices
        print(f"\nTotal Records: {total:,}")


def main():
    parser = argparse.ArgumentParser(
        description="Foodberg Data Pipeline - Collect and import data"
    )
    parser.add_argument(
        "command",
        choices=["collect", "import", "collect-and-import", "status"],
        help="Command to run",
    )

    args = parser.parse_args()

    if args.command == "collect":
        collect_data()
    elif args.command == "import":
        import_data()
    elif args.command == "collect-and-import":
        results = collect_data()
        # Only import if collection succeeded
        if any(s.get("status") == "success" for s in results["sources"].values()):
            import_data()
        else:
            print("\n⚠️  No data collected, skipping import")
    elif args.command == "status":
        show_status()


if __name__ == "__main__":
    main()
