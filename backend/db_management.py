#!/usr/bin/env python3
"""
Database Management Utilities for Foodberg
Backup, export, and maintenance operations
"""

import sys
import shutil
import json
import csv
from pathlib import Path
from datetime import datetime
import argparse

sys.path.insert(0, str(Path(__file__).parent))

from database.manager import DatabaseManager
from database.models import WASDEData, EconomicIndicator, GlobalPrice


def backup_database(output_dir: Path = None):
    """Create a backup of the SQLite database"""
    if output_dir is None:
        output_dir = Path(__file__).parent / "data" / "backups"

    output_dir.mkdir(parents=True, exist_ok=True)

    source = Path(__file__).parent / "data" / "foodberg.db"
    if not source.exists():
        print("Error: Database not found")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = output_dir / f"foodberg_backup_{timestamp}.db"

    shutil.copy2(source, backup_path)

    # Get file size
    size_mb = backup_path.stat().st_size / (1024 * 1024)

    print(f"✓ Backup created: {backup_path.name} ({size_mb:.1f} MB)")
    return backup_path


def export_to_csv(output_dir: Path = None):
    """Export database tables to CSV files"""
    if output_dir is None:
        output_dir = Path(__file__).parent / "data" / "exports"

    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d")
    db = DatabaseManager()

    exports = {}

    with db.get_session() as session:
        # Export Economic Indicators
        print("Exporting economic_indicators...")
        indicators = session.query(EconomicIndicator).all()
        csv_path = output_dir / f"economic_indicators_{timestamp}.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "date",
                    "series_id",
                    "indicator_name",
                    "value",
                    "category",
                    "frequency",
                    "source",
                ]
            )
            for row in indicators:
                writer.writerow(
                    [
                        row.date.strftime("%Y-%m-%d") if row.date else "",
                        row.series_id,
                        row.indicator_name,
                        row.value,
                        row.category,
                        row.frequency,
                        row.source,
                    ]
                )
        exports["economic_indicators"] = {
            "file": csv_path.name,
            "rows": len(indicators),
        }
        print(f"  ✓ {len(indicators):,} records → {csv_path.name}")

        # Export Global Prices
        print("Exporting global_prices...")
        prices = session.query(GlobalPrice).all()
        csv_path = output_dir / f"global_prices_{timestamp}.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["date", "commodity", "price", "currency", "unit", "region", "source"]
            )
            for row in prices:
                writer.writerow(
                    [
                        row.date.strftime("%Y-%m-%d") if row.date else "",
                        row.commodity,
                        row.price,
                        row.currency,
                        row.unit,
                        row.region,
                        row.source,
                    ]
                )
        exports["global_prices"] = {"file": csv_path.name, "rows": len(prices)}
        print(f"  ✓ {len(prices):,} records → {csv_path.name}")

        # Export WASDE (sample - full export would be large)
        print("Exporting wasde_data (summary)...")
        wasde_count = session.query(WASDEData).count()
        exports["wasde_data"] = {
            "rows": wasde_count,
            "note": "Full export available on request",
        }
        print(f"  ℹ {wasde_count:,} records (summary only)")

    # Save export manifest
    manifest_path = output_dir / f"export_manifest_{timestamp}.json"
    with open(manifest_path, "w") as f:
        json.dump(
            {"timestamp": datetime.now().isoformat(), "exports": exports}, f, indent=2
        )

    print(f"\n✓ Export manifest: {manifest_path.name}")
    return exports


def get_statistics():
    """Get database statistics"""
    db = DatabaseManager()

    stats = {"timestamp": datetime.now().isoformat(), "tables": {}}

    with db.get_session() as session:
        # WASDE
        wasde_count = session.query(WASDEData).count()
        stats["tables"]["wasde_data"] = {"count": wasde_count}

        # Economic Indicators
        indicators_count = session.query(EconomicIndicator).count()
        stats["tables"]["economic_indicators"] = {"count": indicators_count}

        # By source
        from sqlalchemy import func

        sources = (
            session.query(EconomicIndicator.source, func.count(EconomicIndicator.id))
            .group_by(EconomicIndicator.source)
            .all()
        )
        stats["tables"]["economic_indicators"]["by_source"] = dict(sources)

        # Global Prices
        prices_count = session.query(GlobalPrice).count()
        stats["tables"]["global_prices"] = {"count": prices_count}

        sources = (
            session.query(GlobalPrice.source, func.count(GlobalPrice.id))
            .group_by(GlobalPrice.source)
            .all()
        )
        stats["tables"]["global_prices"]["by_source"] = dict(sources)

    stats["total_records"] = wasde_count + indicators_count + prices_count

    return stats


def main():
    parser = argparse.ArgumentParser(description="Foodberg Database Management")
    parser.add_argument(
        "command", choices=["backup", "export", "stats"], help="Command to run"
    )
    parser.add_argument("--output", "-o", help="Output directory")

    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else None

    if args.command == "backup":
        backup_database(output_dir)

    elif args.command == "export":
        export_to_csv(output_dir)

    elif args.command == "stats":
        stats = get_statistics()
        print("\n" + "=" * 60)
        print("FOODBERG DATABASE STATISTICS")
        print("=" * 60)
        print(f"\nTimestamp: {stats['timestamp']}")
        print(f"\nTotal Records: {stats['total_records']:,}")
        print("\nBy Table:")
        for table, info in stats["tables"].items():
            print(f"  {table}: {info['count']:,}")
            if "by_source" in info:
                for source, count in info["by_source"].items():
                    print(f"    - {source}: {count:,}")


if __name__ == "__main__":
    main()
