"""
World Bank WDI Importer
Loads World Bank agricultural indicators from Robin's WDI CSV files
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..models import GlobalPrice
from ..manager import DatabaseManager

logger = logging.getLogger(__name__)

# Food-related World Bank indicators to import
FOOD_INDICATORS = {
    "AG.PRD.FOOD.XD": "Food Production Index",
    "AG.PRD.CROP.XD": "Crop Production Index",
    "AG.PRD.LVSK.XD": "Livestock Production Index",
    "AG.LND.CREL.HA": "Land Under Cereal Production (hectares)",
    "AG.PRD.CREL.MT": "Cereal Production (metric tons)",
    "AG.YLD.CREL.KG": "Cereal Yield (kg/hectare)",
    "NV.AGR.TOTL.ZS": "Agriculture Value Added (% of GDP)",
    "TM.VAL.FOOD.ZS.UN": "Food Imports (% of merchandise)",
    "TX.VAL.FOOD.ZS.UN": "Food Exports (% of merchandise)",
}

# Focus on key countries/regions
TARGET_COUNTRIES = {"USA", "WLD", "EUU", "CHN", "IND", "BRA", "ARG", "AUS", "CAN"}


class WorldBankImporter:
    def __init__(self, robin_data_path: Optional[str] = None):
        if robin_data_path is None:
            robin_data_path = "D:/Arcanum/Council/Robin/DATA/WorldBank/WDI_CSV"

        self.robin_data_path = Path(robin_data_path)
        if not self.robin_data_path.exists():
            raise FileNotFoundError(f"Robin World Bank data not found: {robin_data_path}")

        self.db_manager = None

    def set_database_manager(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def find_wdi_csv(self) -> Path:
        csv_files = list(self.robin_data_path.glob("*WDICSV*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No WDI CSV files found in {self.robin_data_path}")
        return sorted(csv_files)[-1]

    def import_all(self, batch_size: int = 500) -> Dict[str, int]:
        if not self.db_manager:
            raise ValueError("Database manager not set. Call set_database_manager() first.")

        csv_file = self.find_wdi_csv()

        stats = {
            "file": str(csv_file.name),
            "total_records": 0,
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "indicators": {},
        }

        print(f"\n{'='*80}")
        print(f"WORLD BANK WDI IMPORT")
        print(f"Source: {csv_file.name}")
        print(f"{'='*80}\n")

        try:
            batch = []
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    indicator_code = row.get("Indicator Code", "")
                    country_code = row.get("Country Code", "")
                    country_name = row.get("Country Name", "")

                    if indicator_code not in FOOD_INDICATORS:
                        continue
                    if country_code not in TARGET_COUNTRIES:
                        continue

                    indicator_name = FOOD_INDICATORS[indicator_code]

                    # Years are columns from 1960 to 2024+
                    for year in range(1990, 2026):
                        value_str = row.get(str(year), "").strip()
                        if not value_str:
                            continue
                        try:
                            value = float(value_str)
                        except ValueError:
                            continue

                        batch.append({
                            "commodity": indicator_name,
                            "price": value,
                            "currency": "Index" if "Index" in indicator_name else "USD",
                            "unit": "index" if "Index" in indicator_name else "various",
                            "region": country_name,
                            "country": country_code,
                            "date": datetime(year, 7, 1),  # Mid-year for annual data
                            "source": "World Bank",
                            "indicator_code": indicator_code,
                        })
                        stats["total_records"] += 1

                        if indicator_code not in stats["indicators"]:
                            stats["indicators"][indicator_code] = 0
                        stats["indicators"][indicator_code] += 1

                    if len(batch) >= batch_size:
                        result = self._insert_batch(batch)
                        stats["imported"] += result["inserted"]
                        stats["skipped"] += result["skipped"]
                        batch = []

            if batch:
                result = self._insert_batch(batch)
                stats["imported"] += result["inserted"]
                stats["skipped"] += result["skipped"]

            print("Indicator breakdown:")
            for code, count in sorted(stats["indicators"].items()):
                name = FOOD_INDICATORS.get(code, code)
                print(f"  {name}: {count} records")

            print(f"\n{'='*80}")
            print(f"WORLD BANK IMPORT COMPLETE")
            print(f"{'='*80}")
            print(f"Total records: {stats['total_records']}")
            print(f"Imported: {stats['imported']}")
            print(f"Skipped (duplicates): {stats['skipped']}")
            print()

        except Exception as e:
            logger.error(f"World Bank import failed: {e}")
            stats["errors"] += 1
            import traceback
            traceback.print_exc()

        return stats

    def _insert_batch(self, batch: List[Dict]) -> Dict[str, int]:
        result = {"inserted": 0, "skipped": 0}

        with self.db_manager.get_session() as session:
            for record_data in batch:
                existing = (
                    session.query(GlobalPrice)
                    .filter(
                        GlobalPrice.commodity == record_data["commodity"],
                        GlobalPrice.date == record_data["date"],
                        GlobalPrice.country == record_data["country"],
                        GlobalPrice.source == "World Bank",
                    )
                    .first()
                )

                if existing:
                    result["skipped"] += 1
                    continue

                record = GlobalPrice(**record_data)
                session.add(record)
                result["inserted"] += 1

            session.commit()

        return result
