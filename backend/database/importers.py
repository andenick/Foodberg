"""
Database Importers for Foodberg
Import data from Robin's data store into Foodberg's SQLite database.

This module provides importers for:
- WASDE agricultural data
- FRED economic indicators
- BLS price indices
- FAO Food Price Index
- World Bank commodity prices
- USDA Market News prices
"""

import json
import csv
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import (
    Base,
    WASDEData,
    MarketPrice,
    EconomicIndicator,
    GlobalPrice,
    RetailPrice,
    DataSourceSync,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class RobinDataImporter:
    """
    Import data from Robin's data store into Foodberg's database.
    """

    ROBIN_BASE = Path("D:/Arcanum/Council/Robin")

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the importer with database connection."""
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / "data" / "foodberg.db")

        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)

        self.Session = sessionmaker(bind=self.engine)

        # Robin data paths
        self.paths = {
            "wasde": self.ROBIN_BASE / "DATA" / "USDA_WASDE",
            "fred": self.ROBIN_BASE / "DATA" / "FRED" / "fred_data",
            "bls": self.ROBIN_BASE / "DATA" / "BLS",
            "fao": self.ROBIN_BASE / "DATA" / "FAO",
            "worldbank": self.ROBIN_BASE / "DATA" / "WorldBank" / "WDI_CSV",
            "imf": self.ROBIN_BASE / "DATA" / "IMF",
        }

    def _update_sync_status(
        self, source: str, status: str, records: int, error: str = None
    ):
        """Update the sync status for a data source."""
        session = self.Session()
        try:
            sync = session.query(DataSourceSync).filter_by(source_name=source).first()
            if sync:
                sync.last_sync_time = datetime.utcnow()
                sync.last_sync_status = status
                sync.records_synced = records
                sync.error_message = error
            else:
                sync = DataSourceSync(
                    source_name=source,
                    last_sync_time=datetime.utcnow(),
                    last_sync_status=status,
                    records_synced=records,
                    error_message=error,
                )
                session.add(sync)
            session.commit()
        finally:
            session.close()

    # ==================== WASDE IMPORTER ====================

    def import_wasde(self, commodities: List[str] = None) -> Dict[str, int]:
        """
        Import WASDE data from Robin into Foodberg database.

        Args:
            commodities: List of commodities to import (None = all available)

        Returns:
            Dict with import statistics
        """
        wasde_path = self.paths["wasde"]
        if not wasde_path.exists():
            print(f"[WASDE] Path not found: {wasde_path}")
            return {"error": "WASDE path not found"}

        session = self.Session()
        stats = {"imported": 0, "skipped": 0, "errors": 0}

        try:
            # Find all WASDE JSON files
            json_files = list(wasde_path.glob("wasde_*.json"))

            if commodities:
                json_files = [
                    f
                    for f in json_files
                    if any(c in f.name.lower() for c in commodities)
                ]

            print(f"[WASDE] Found {len(json_files)} files to process")

            for json_file in json_files:
                try:
                    # Read file in chunks due to large size
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    commodity = data.get(
                        "commodity", json_file.stem.replace("wasde_", "")
                    )
                    records = data.get("data", [])

                    print(f"[WASDE] Processing {commodity}: {len(records)} records")

                    batch = []
                    for record in records[:10000]:  # Limit initial import
                        try:
                            wasde_record = WASDEData(
                                commodity=record.get(
                                    "commodity_desc", commodity
                                ).upper(),
                                statistic_category=record.get("statisticcat_desc", ""),
                                value=str(record.get("value", "")),
                                numeric_value=self._parse_numeric(record.get("value")),
                                unit=record.get("unit_desc", ""),
                                location=record.get("state_name", "US TOTAL"),
                                state_code=record.get("state_alpha", ""),
                                agg_level=record.get("agg_level_desc", ""),
                                year=self._parse_year(record.get("year")),
                                reference_period=record.get(
                                    "reference_period_desc", ""
                                ),
                                short_desc=record.get("short_desc", ""),
                                source_desc=record.get("source_desc", "SURVEY"),
                                sector=record.get("sector_desc", ""),
                                group_desc=record.get("group_desc", ""),
                                class_desc=record.get("class_desc", ""),
                                freq_desc=record.get("freq_desc", "ANNUAL"),
                            )
                            batch.append(wasde_record)
                            stats["imported"] += 1

                            # Commit in batches
                            if len(batch) >= 1000:
                                session.bulk_save_objects(batch)
                                session.commit()
                                batch = []

                        except Exception as e:
                            stats["errors"] += 1
                            if stats["errors"] < 5:
                                print(f"[WASDE] Record error: {e}")

                    # Commit remaining
                    if batch:
                        session.bulk_save_objects(batch)
                        session.commit()

                except Exception as e:
                    print(f"[WASDE] File error {json_file}: {e}")
                    stats["errors"] += 1

            self._update_sync_status("WASDE", "SUCCESS", stats["imported"])

        except Exception as e:
            print(f"[WASDE] Import error: {e}")
            self._update_sync_status("WASDE", "FAILED", 0, str(e))
            stats["error"] = str(e)
        finally:
            session.close()

        print(f"[WASDE] Import complete: {stats}")
        return stats

    # ==================== FAO IMPORTER ====================

    def import_fao(self) -> Dict[str, int]:
        """
        Import FAO Food Price Index data into GlobalPrice table.
        """
        fao_path = self.paths["fao"]
        if not fao_path.exists():
            print(f"[FAO] Path not found: {fao_path}")
            return {"error": "FAO path not found"}

        session = self.Session()
        stats = {"imported": 0, "skipped": 0, "errors": 0}

        try:
            # Find latest FAO JSON
            json_files = list(fao_path.glob("fao_food_price_index_*.json"))
            if not json_files:
                return {"error": "No FAO data files found"}

            latest = max(json_files, key=lambda f: f.stat().st_mtime)
            print(f"[FAO] Loading {latest}")

            with open(latest, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Process each category
            for category, values in data.get("categories", {}).items():
                for record in values:
                    try:
                        # Parse date from FAO format
                        date_str = record.get("date", "")
                        date_val = self._parse_fao_date(date_str)

                        if date_val and record.get("value"):
                            price_record = GlobalPrice(
                                commodity=f"FAO_{category.upper()}_INDEX",
                                price=float(record["value"]),
                                currency="INDEX",
                                unit="base 2014-2016=100",
                                region="Global",
                                date=date_val,
                                source="FAO",
                                indicator_code=record.get("index_type", category),
                            )
                            session.add(price_record)
                            stats["imported"] += 1

                    except Exception as e:
                        stats["errors"] += 1
                        if stats["errors"] < 5:
                            print(f"[FAO] Record error: {e}")

            session.commit()
            self._update_sync_status("FAO", "SUCCESS", stats["imported"])

        except Exception as e:
            print(f"[FAO] Import error: {e}")
            self._update_sync_status("FAO", "FAILED", 0, str(e))
            stats["error"] = str(e)
        finally:
            session.close()

        print(f"[FAO] Import complete: {stats}")
        return stats

    # ==================== FRED IMPORTER ====================

    def import_fred(self, series_ids: List[str] = None) -> Dict[str, int]:
        """
        Import FRED economic indicators into EconomicIndicator table.

        Args:
            series_ids: Specific series to import (None = food-related series)
        """
        fred_db = self.paths["fred"] / "fred_data.db"
        if not fred_db.exists():
            print(f"[FRED] Database not found: {fred_db}")
            return {"error": "FRED database not found"}

        # Default food-related series
        if series_ids is None:
            series_ids = [
                "CPIUFDSL",  # CPI for Food
                "CUSR0000SAF11",  # CPI: Food at Home
                "CUSR0000SEFV",  # CPI: Food Away from Home
                "WPU01",  # PPI: Farm Products
                "WPU02",  # PPI: Processed Foods
            ]

        session = self.Session()
        stats = {"imported": 0, "skipped": 0, "errors": 0}

        try:
            # Connect to FRED SQLite database
            fred_conn = sqlite3.connect(str(fred_db))
            fred_cursor = fred_conn.cursor()

            # Try to find the correct table name
            fred_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in fred_cursor.fetchall()]
            print(f"[FRED] Available tables: {tables}")

            # Query each series
            for series_id in series_ids:
                for table in tables:
                    try:
                        fred_cursor.execute(
                            f"""
                            SELECT date, value FROM {table}
                            WHERE series_id = ? OR id LIKE ?
                            ORDER BY date DESC LIMIT 1000
                        """,
                            (series_id, f"%{series_id}%"),
                        )

                        rows = fred_cursor.fetchall()
                        if rows:
                            print(f"[FRED] Found {len(rows)} records for {series_id}")

                            for date_val, value in rows:
                                try:
                                    indicator = EconomicIndicator(
                                        indicator_name=series_id,
                                        series_id=series_id,
                                        value=float(value) if value else 0,
                                        date=self._parse_date(date_val),
                                        category=(
                                            "CPI"
                                            if "CPI" in series_id or "CUUR" in series_id
                                            else "PPI"
                                        ),
                                        frequency="Monthly",
                                        source="FRED",
                                    )
                                    session.add(indicator)
                                    stats["imported"] += 1
                                except Exception as e:
                                    stats["errors"] += 1
                            break
                    except sqlite3.OperationalError:
                        continue

            session.commit()
            fred_conn.close()
            self._update_sync_status("FRED", "SUCCESS", stats["imported"])

        except Exception as e:
            print(f"[FRED] Import error: {e}")
            self._update_sync_status("FRED", "FAILED", 0, str(e))
            stats["error"] = str(e)
        finally:
            session.close()

        print(f"[FRED] Import complete: {stats}")
        return stats

    # ==================== WORLD BANK IMPORTER ====================

    def import_worldbank(self) -> Dict[str, int]:
        """
        Import World Bank commodity data into GlobalPrice table.
        """
        wb_path = self.paths["worldbank"]
        if not wb_path.exists():
            print(f"[WorldBank] Path not found: {wb_path}")
            return {"error": "World Bank path not found"}

        session = self.Session()
        stats = {"imported": 0, "skipped": 0, "errors": 0}

        try:
            # Food/agriculture related indicators
            food_keywords = [
                "food",
                "agriculture",
                "cereal",
                "meat",
                "dairy",
                "commodity",
                "crop",
                "livestock",
                "price",
            ]

            for csv_file in wb_path.glob("*.csv"):
                try:
                    with open(csv_file, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)

                        for row in reader:
                            indicator = row.get("Indicator Name", "").lower()

                            # Filter for food-related indicators
                            if not any(kw in indicator for kw in food_keywords):
                                continue

                            country = row.get("Country Name", "World")
                            indicator_code = row.get("Indicator Code", "")

                            # Process year columns (typically 1960-2023)
                            for col, value in row.items():
                                if col.isdigit() and value:
                                    try:
                                        year = int(col)
                                        price_val = float(value)

                                        price_record = GlobalPrice(
                                            commodity=row.get("Indicator Name", "")[
                                                :100
                                            ],
                                            price=price_val,
                                            currency="USD",
                                            region=country,
                                            country=country,
                                            date=datetime(year, 1, 1),
                                            source="World Bank",
                                            indicator_code=indicator_code,
                                        )
                                        session.add(price_record)
                                        stats["imported"] += 1

                                    except (ValueError, TypeError):
                                        stats["skipped"] += 1

                            # Commit in batches
                            if stats["imported"] % 1000 == 0 and stats["imported"] > 0:
                                session.commit()

                except Exception as e:
                    print(f"[WorldBank] File error {csv_file}: {e}")
                    stats["errors"] += 1

            session.commit()
            self._update_sync_status("WorldBank", "SUCCESS", stats["imported"])

        except Exception as e:
            print(f"[WorldBank] Import error: {e}")
            self._update_sync_status("WorldBank", "FAILED", 0, str(e))
            stats["error"] = str(e)
        finally:
            session.close()

        print(f"[WorldBank] Import complete: {stats}")
        return stats

    # ==================== BLS IMPORTER ====================

    def import_bls(self) -> Dict[str, int]:
        """
        Import BLS CPI data into EconomicIndicator table.
        """
        bls_path = self.paths["bls"]
        if not bls_path.exists():
            print(f"[BLS] Path not found: {bls_path}")
            return {"error": "BLS path not found"}

        session = self.Session()
        stats = {"imported": 0, "skipped": 0, "errors": 0}

        try:
            # Look for BLS collection summary
            summary_files = list(bls_path.glob("*collection_summary*.json"))

            for summary_file in summary_files:
                try:
                    with open(summary_file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # Process series data
                    for series_id, series_data in data.get("series", {}).items():
                        if "data" not in series_data:
                            continue

                        for record in series_data["data"]:
                            try:
                                indicator = EconomicIndicator(
                                    indicator_name=series_data.get("name", series_id),
                                    series_id=series_id,
                                    value=float(record.get("value", 0)),
                                    date=self._parse_bls_date(record),
                                    category="CPI" if "CU" in series_id else "Other",
                                    frequency="Monthly",
                                    source="BLS",
                                )
                                session.add(indicator)
                                stats["imported"] += 1
                            except Exception as e:
                                stats["errors"] += 1

                except Exception as e:
                    print(f"[BLS] File error {summary_file}: {e}")
                    stats["errors"] += 1

            session.commit()
            self._update_sync_status("BLS", "SUCCESS", stats["imported"])

        except Exception as e:
            print(f"[BLS] Import error: {e}")
            self._update_sync_status("BLS", "FAILED", 0, str(e))
            stats["error"] = str(e)
        finally:
            session.close()

        print(f"[BLS] Import complete: {stats}")
        return stats

    # ==================== HELPER METHODS ====================

    def _parse_numeric(self, value: Any) -> Optional[float]:
        """Parse a value to float, handling various formats."""
        if value is None:
            return None
        try:
            if isinstance(value, (int, float)):
                return float(value)
            # Remove commas and parse
            clean = str(value).replace(",", "").strip()
            return float(clean)
        except (ValueError, TypeError):
            return None

    def _parse_year(self, value: Any) -> Optional[int]:
        """Parse a year value."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _parse_date(self, value: str) -> Optional[datetime]:
        """Parse a date string to datetime."""
        if not value:
            return None

        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y-%m",
            "%Y",
            "%m/%d/%Y",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(value).strip(), fmt)
            except ValueError:
                continue

        return None

    def _parse_fao_date(self, value: str) -> Optional[datetime]:
        """Parse FAO date format (typically 'YYYY-MM' or 'Jan-2020')."""
        if not value:
            return None

        # Try standard formats
        formats = [
            "%Y-%m",
            "%b-%Y",
            "%B-%Y",
            "%m/%Y",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(value).strip(), fmt)
            except ValueError:
                continue

        return None

    def _parse_bls_date(self, record: Dict) -> Optional[datetime]:
        """Parse BLS date from year/period fields."""
        try:
            year = int(record.get("year", 0))
            period = record.get("period", "M01")

            # BLS periods: M01-M12 for monthly, A01 for annual
            if period.startswith("M"):
                month = int(period[1:])
            else:
                month = 1

            return datetime(year, month, 1)
        except (ValueError, TypeError):
            return None

    # ==================== MAIN IMPORT ====================

    def import_all(self, sources: List[str] = None) -> Dict[str, Dict]:
        """
        Import data from all (or specified) sources.

        Args:
            sources: List of sources to import (None = all)
                     Options: 'wasde', 'fao', 'fred', 'worldbank', 'bls'
        """
        all_sources = ["wasde", "fao", "fred", "worldbank", "bls"]

        if sources is None:
            sources = all_sources

        results = {}

        for source in sources:
            print(f"\n{'='*60}")
            print(f"IMPORTING: {source.upper()}")
            print("=" * 60)

            if source == "wasde":
                # Import only a few commodities for testing
                results[source] = self.import_wasde(
                    ["wheat", "corn", "rice", "beef", "milk"]
                )
            elif source == "fao":
                results[source] = self.import_fao()
            elif source == "fred":
                results[source] = self.import_fred()
            elif source == "worldbank":
                results[source] = self.import_worldbank()
            elif source == "bls":
                results[source] = self.import_bls()
            else:
                print(f"Unknown source: {source}")
                results[source] = {"error": "Unknown source"}

        return results

    def get_sync_status(self) -> List[Dict]:
        """Get sync status for all data sources."""
        session = self.Session()
        try:
            syncs = session.query(DataSourceSync).all()
            return [
                {
                    "source": s.source_name,
                    "last_sync": (
                        s.last_sync_time.isoformat() if s.last_sync_time else None
                    ),
                    "status": s.last_sync_status,
                    "records": s.records_synced,
                    "error": s.error_message,
                }
                for s in syncs
            ]
        finally:
            session.close()


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Import Robin data into Foodberg database"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["wasde", "fao", "fred", "worldbank", "bls", "all"],
        default=["all"],
        help="Data sources to import",
    )
    parser.add_argument("--status", action="store_true", help="Show sync status only")

    args = parser.parse_args()

    importer = RobinDataImporter()

    if args.status:
        print("\n" + "=" * 60)
        print("DATA SOURCE SYNC STATUS")
        print("=" * 60)
        for status in importer.get_sync_status():
            print(f"\n{status['source']}:")
            print(f"  Last sync: {status['last_sync']}")
            print(f"  Status: {status['status']}")
            print(f"  Records: {status['records']}")
            if status["error"]:
                print(f"  Error: {status['error']}")
    else:
        sources = None if "all" in args.sources else args.sources
        results = importer.import_all(sources)

        print("\n" + "=" * 60)
        print("IMPORT SUMMARY")
        print("=" * 60)
        for source, stats in results.items():
            print(f"\n{source}:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
