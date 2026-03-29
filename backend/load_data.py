#!/usr/bin/env python3
"""
Foodberg Data Loader CLI
Unified interface to load data from all Robin sources into Foodberg database

Usage:
    python load_data.py --all          # Load from all sources
    python load_data.py --sources wasde fao bls fred
    python load_data.py --status       # Show database status
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from database.manager import DatabaseManager
from database.importers import WASDEImporter, FAOImporter, BLSImporter, FREDImporter


def get_database_status(db_manager: DatabaseManager) -> dict:
    """Get current database status"""
    from database.models import WASDEData, EconomicIndicator, GlobalPrice
    from sqlalchemy import text, func

    status = {}

    with db_manager.get_session() as session:
        status["wasde"] = session.query(WASDEData).count()
        status["economic_indicators"] = session.query(EconomicIndicator).count()
        status["global_prices"] = session.query(GlobalPrice).count()

        # Get source breakdown for economic_indicators
        sources = (
            session.query(EconomicIndicator.source, func.count(EconomicIndicator.id))
            .group_by(EconomicIndicator.source)
            .all()
        )
        status["indicator_sources"] = {s[0]: s[1] for s in sources}

        # Get source breakdown for global_prices
        sources = (
            session.query(GlobalPrice.source, func.count(GlobalPrice.id))
            .group_by(GlobalPrice.source)
            .all()
        )
        status["global_sources"] = {s[0]: s[1] for s in sources}

    return status


def print_status(status: dict):
    """Print formatted database status"""
    print(f"\n{'='*60}")
    print("FOODBERG DATABASE STATUS")
    print(f"{'='*60}\n")

    print("Table Counts:")
    print(f"  WASDE Data:          {status['wasde']:,} records")
    print(f"  Economic Indicators: {status['economic_indicators']:,} records")
    print(f"  Global Prices:       {status['global_prices']:,} records")

    if status.get("indicator_sources"):
        print("\nEconomic Indicator Sources:")
        for source, count in sorted(status["indicator_sources"].items()):
            print(f"  {source}: {count:,} records")

    if status.get("global_sources"):
        print("\nGlobal Price Sources:")
        for source, count in sorted(status["global_sources"].items()):
            print(f"  {source}: {count:,} records")

    total = status["wasde"] + status["economic_indicators"] + status["global_prices"]
    print(f"\nTotal Records: {total:,}")
    print()


def load_wasde(db_manager: DatabaseManager):
    """Load WASDE data"""
    print("\n" + "=" * 60)
    print("Loading WASDE Data...")
    print("=" * 60)

    try:
        importer = WASDEImporter()
        importer.set_database_manager(db_manager)
        stats = importer.import_all_commodities()
        print(f"✅ WASDE: {stats.get('total_records', 0):,} records")
        return stats
    except Exception as e:
        print(f"❌ WASDE import failed: {e}")
        return {"error": str(e)}


def load_fao(db_manager: DatabaseManager):
    """Load FAO Food Price Index data"""
    print("\n" + "=" * 60)
    print("Loading FAO Data...")
    print("=" * 60)

    try:
        importer = FAOImporter()
        importer.set_database_manager(db_manager)
        stats = importer.import_all()
        print(f"✅ FAO: {stats.get('imported', 0):,} records imported")
        return stats
    except Exception as e:
        print(f"❌ FAO import failed: {e}")
        return {"error": str(e)}


def load_bls(db_manager: DatabaseManager):
    """Load BLS CPI data"""
    print("\n" + "=" * 60)
    print("Loading BLS Data...")
    print("=" * 60)

    try:
        importer = BLSImporter()
        importer.set_database_manager(db_manager)
        stats = importer.import_all()
        print(f"✅ BLS: {stats.get('imported', 0):,} records imported")
        return stats
    except Exception as e:
        print(f"❌ BLS import failed: {e}")
        return {"error": str(e)}


def load_fred(db_manager: DatabaseManager):
    """Load FRED economic data"""
    print("\n" + "=" * 60)
    print("Loading FRED Data...")
    print("=" * 60)

    try:
        importer = FREDImporter()
        importer.set_database_manager(db_manager)
        stats = importer.import_all()
        print(f"✅ FRED: {stats.get('imported', 0):,} records imported")
        return stats
    except Exception as e:
        print(f"❌ FRED import failed: {e}")
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Foodberg Data Loader - Import data from Robin sources"
    )
    parser.add_argument(
        "--all", action="store_true", help="Load from all available sources"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["wasde", "fao", "bls", "fred"],
        help="Specific sources to load",
    )
    parser.add_argument(
        "--status", action="store_true", help="Show current database status"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database tables (run first time)",
    )

    args = parser.parse_args()

    # Initialize database manager
    db_manager = DatabaseManager()

    if args.init_db:
        print("Initializing database tables...")
        db_manager.create_tables()
        print("✅ Database tables created")
        return

    if args.status:
        status = get_database_status(db_manager)
        print_status(status)
        return

    if not args.all and not args.sources:
        parser.print_help()
        print("\n⚠️  Please specify --all or --sources")
        return

    # Determine which sources to load
    sources = ["wasde", "fao", "bls", "fred"] if args.all else args.sources

    print(f"\n{'#'*60}")
    print(f"# FOODBERG DATA LOADING")
    print(f"# Sources: {', '.join(sources)}")
    print(f"{'#'*60}")

    results = {}

    # Load each source
    loaders = {
        "wasde": load_wasde,
        "fao": load_fao,
        "bls": load_bls,
        "fred": load_fred,
    }

    for source in sources:
        if source in loaders:
            results[source] = loaders[source](db_manager)

    # Print summary
    print(f"\n{'='*60}")
    print("LOADING COMPLETE - SUMMARY")
    print(f"{'='*60}\n")

    for source, result in results.items():
        if "error" in result:
            print(f"❌ {source.upper()}: FAILED - {result['error']}")
        else:
            count = result.get("imported", result.get("total_records", 0))
            print(f"✅ {source.upper()}: {count:,} records")

    # Show final status
    status = get_database_status(db_manager)
    print_status(status)


if __name__ == "__main__":
    main()
