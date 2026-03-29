#!/usr/bin/env python3
"""
Foodberg Production Startup Script
Initializes database, collects data if needed, and starts the server
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def check_database():
    """Check if database exists and has data"""
    from database.manager import DatabaseManager
    from database.models import WASDEData, EconomicIndicator, GlobalPrice

    db = DatabaseManager()

    with db.get_session() as session:
        wasde = session.query(WASDEData).count()
        indicators = session.query(EconomicIndicator).count()
        global_prices = session.query(GlobalPrice).count()

    return {
        "wasde": wasde,
        "indicators": indicators,
        "global_prices": global_prices,
        "total": wasde + indicators + global_prices,
    }


def check_data_freshness():
    """Check when data was last collected"""
    data_dir = Path(__file__).parent / "data" / "collected"
    summary_file = data_dir / "collection_summary.json"

    if not summary_file.exists():
        return None

    import json

    with open(summary_file) as f:
        summary = json.load(f)

    timestamp = summary.get("timestamp")
    if timestamp:
        return datetime.fromisoformat(timestamp)
    return None


def collect_fresh_data():
    """Collect fresh data from APIs"""
    print("Collecting fresh data from APIs...")
    from data_sources.collectors import collect_all_data

    return collect_all_data()


def import_data():
    """Import collected data to database"""
    print("Importing data to database...")
    from database.manager import DatabaseManager
    from database.importers.standalone_importers import (
        StandaloneFAOImporter,
        StandaloneFREDImporter,
        StandaloneBLSImporter,
    )

    db = DatabaseManager()

    # FAO
    try:
        fao = StandaloneFAOImporter()
        fao.set_database_manager(db)
        fao.import_all()
    except Exception as e:
        print(f"FAO import error: {e}")

    # FRED
    try:
        fred = StandaloneFREDImporter()
        fred.set_database_manager(db)
        fred.import_all()
    except Exception as e:
        print(f"FRED import error: {e}")

    # BLS
    try:
        bls = StandaloneBLSImporter()
        bls.set_database_manager(db)
        bls.import_all()
    except Exception as e:
        print(f"BLS import error: {e}")


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server"""
    import uvicorn

    print(f"\n{'='*60}")
    print(f"Starting Foodberg API Server")
    print(f"Host: {host}:{port}")
    print(f"Docs: http://{host}:{port}/docs")
    print(f"{'='*60}\n")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("ENV", "development") == "development",
        log_level="info",
    )


def main():
    parser = argparse.ArgumentParser(description="Foodberg Production Startup")
    parser.add_argument(
        "--skip-data-check", action="store_true", help="Skip data freshness check"
    )
    parser.add_argument(
        "--force-collect", action="store_true", help="Force fresh data collection"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", 8000)),
        help="Server port (default: 8000)",
    )
    parser.add_argument(
        "--init-only",
        action="store_true",
        help="Initialize data only, do not start server",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("FOODBERG PRODUCTION STARTUP")
    print("=" * 60)

    # Step 1: Check database
    print("\n[1/4] Checking database...")
    db_status = check_database()
    print(f"  Database records: {db_status['total']:,}")

    # Step 2: Check data freshness
    if not args.skip_data_check:
        print("\n[2/4] Checking data freshness...")
        last_collection = check_data_freshness()

        if last_collection:
            age = datetime.now() - last_collection
            print(f"  Last collection: {last_collection.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Age: {age.days} days, {age.seconds // 3600} hours")

            # Collect new data if older than 1 day or forced
            if age > timedelta(days=1) or args.force_collect:
                print("  → Data is stale, collecting fresh data...")
                collect_fresh_data()
                import_data()
        else:
            print("  → No previous collection found, collecting data...")
            collect_fresh_data()
            import_data()
    else:
        print("\n[2/4] Skipping data check (--skip-data-check)")

    # Step 3: Verify database after import
    print("\n[3/4] Verifying database...")
    db_status = check_database()
    print(f"  WASDE:      {db_status['wasde']:,} records")
    print(f"  Indicators: {db_status['indicators']:,} records")
    print(f"  Prices:     {db_status['global_prices']:,} records")
    print(f"  Total:      {db_status['total']:,} records")

    if db_status["total"] == 0:
        print("\n⚠️  WARNING: Database is empty!")
        print("  Run: python data_pipeline.py collect-and-import")

    # Step 4: Start server
    if not args.init_only:
        print("\n[4/4] Starting server...")
        start_server(args.host, args.port)
    else:
        print("\n[4/4] Initialization complete (--init-only)")
        print("  Run: uvicorn main:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()
