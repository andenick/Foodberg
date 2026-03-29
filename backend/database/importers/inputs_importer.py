"""
Inputs Folder Importer
Loads retail commodity price data from Foodberg's Inputs/ JSON files
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..models import RetailPrice
from ..manager import DatabaseManager

logger = logging.getLogger(__name__)


class InputsImporter:
    def __init__(self, inputs_path: Optional[str] = None):
        if inputs_path is None:
            inputs_path = str(
                Path(__file__).parent.parent.parent.parent / "Inputs"
            )

        self.inputs_path = Path(inputs_path)
        if not self.inputs_path.exists():
            raise FileNotFoundError(f"Inputs directory not found: {inputs_path}")

        self.db_manager = None

    def set_database_manager(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def import_all(self, batch_size: int = 100) -> Dict[str, int]:
        if not self.db_manager:
            raise ValueError("Database manager not set. Call set_database_manager() first.")

        stats = {
            "total_records": 0,
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "commodities": [],
        }

        print(f"\n{'='*80}")
        print(f"INPUTS FOLDER RETAIL PRICE IMPORT")
        print(f"Source: {self.inputs_path}")
        print(f"{'='*80}\n")

        json_files = sorted(self.inputs_path.glob("*.json"))
        print(f"Found {len(json_files)} JSON files")

        batch = []
        for json_file in json_files:
            if "collection_summary" in json_file.name or "README" in json_file.name:
                continue

            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if not data.get("success", False):
                    continue

                commodity = data.get("commodity", json_file.stem.split("_")[1] if "_" in json_file.stem else json_file.stem)
                price = data.get("price")
                raw = data.get("raw_data", {})

                if price is None or price == 0:
                    continue

                date_str = raw.get("lastUpdated", "2025-09-25")
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    date_obj = datetime(2025, 9, 25)

                record = {
                    "food_item": commodity,
                    "price": float(price),
                    "unit": raw.get("unit", "lb"),
                    "store_type": "Retail",
                    "location": "National Average",
                    "state": None,
                    "country": "USA",
                    "date": date_obj,
                    "source": raw.get("source", "USDA"),
                    "brand": None,
                    "quality_grade": raw.get("category", "Standard"),
                }

                batch.append(record)
                stats["total_records"] += 1
                stats["commodities"].append(commodity)

            except Exception as e:
                logger.warning(f"Error processing {json_file.name}: {e}")
                stats["errors"] += 1

        if batch:
            result = self._insert_batch(batch)
            stats["imported"] += result["inserted"]
            stats["skipped"] += result["skipped"]

        print(f"Commodities processed: {len(stats['commodities'])}")
        print(f"\n{'='*80}")
        print(f"INPUTS IMPORT COMPLETE")
        print(f"{'='*80}")
        print(f"Total records: {stats['total_records']}")
        print(f"Imported: {stats['imported']}")
        print(f"Skipped (duplicates): {stats['skipped']}")
        print(f"Errors: {stats['errors']}")
        print()

        return stats

    def _insert_batch(self, batch: List[Dict]) -> Dict[str, int]:
        result = {"inserted": 0, "skipped": 0}

        with self.db_manager.get_session() as session:
            for record_data in batch:
                existing = (
                    session.query(RetailPrice)
                    .filter(
                        RetailPrice.food_item == record_data["food_item"],
                        RetailPrice.date == record_data["date"],
                        RetailPrice.source == record_data["source"],
                    )
                    .first()
                )

                if existing:
                    result["skipped"] += 1
                    continue

                record = RetailPrice(**record_data)
                session.add(record)
                result["inserted"] += 1

            session.commit()

        return result
