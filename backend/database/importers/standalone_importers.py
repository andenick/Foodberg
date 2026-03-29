"""
Standalone Data Importers for Foodberg
Imports from Foodberg's own collected JSON files (not Robin dependency)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..models import GlobalPrice, EconomicIndicator
from ..manager import DatabaseManager

logger = logging.getLogger(__name__)


# Default data directory
DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "collected"


class StandaloneFAOImporter:
    """
    Import FAO Food Price Index from Foodberg's own collected data
    """

    CATEGORY_MAPPING = {
        "food": "FAO Food Price Index - Overall",
        "meat": "FAO Food Price Index - Meat",
        "dairy": "FAO Food Price Index - Dairy",
        "cereals": "FAO Food Price Index - Cereals",
        "oils": "FAO Food Price Index - Oils",
        "sugar": "FAO Food Price Index - Sugar",
    }

    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            self.data_path = DEFAULT_DATA_DIR / "fao_data.json"
        else:
            self.data_path = Path(data_path)

        self.db_manager = None

    def set_database_manager(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def import_all(self, batch_size: int = 500) -> Dict[str, int]:
        """Import all FAO data"""
        if not self.db_manager:
            raise ValueError("Database manager not set")

        if not self.data_path.exists():
            raise FileNotFoundError(f"FAO data not found: {self.data_path}")

        with open(self.data_path) as f:
            data = json.load(f)

        stats = {"imported": 0, "skipped": 0, "errors": 0}

        print(f"\n{'='*60}")
        print("FAO FOOD PRICE INDEX IMPORT")
        print(f"Source: {self.data_path.name}")
        print(f"{'='*60}\n")

        batch = []
        for category, records in data.items():
            if category not in self.CATEGORY_MAPPING:
                continue

            commodity_name = self.CATEGORY_MAPPING[category]

            for record in records:
                try:
                    date_obj = datetime.strptime(record["date"], "%Y-%m")

                    batch.append(
                        {
                            "date": date_obj,
                            "commodity": commodity_name,
                            "price": float(record["value"]),
                            "currency": "index",
                            "unit": "2014-2016=100",
                            "region": "Global",
                            "source": "FAO",
                            "indicator_code": f"fao_{category}",
                        }
                    )

                    if len(batch) >= batch_size:
                        result = self._insert_batch(batch)
                        stats["imported"] += result["inserted"]
                        stats["skipped"] += result["skipped"]
                        batch = []

                except Exception as e:
                    stats["errors"] += 1
                    logger.warning(f"Error processing record: {e}")

            print(f"  {category}: {len(records)} records")

        # Insert remaining
        if batch:
            result = self._insert_batch(batch)
            stats["imported"] += result["inserted"]
            stats["skipped"] += result["skipped"]

        print(f"\n{'='*60}")
        print(
            f"Imported: {stats['imported']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}"
        )
        print(f"{'='*60}\n")

        return stats

    def _insert_batch(self, batch: List[Dict]) -> Dict[str, int]:
        result = {"inserted": 0, "skipped": 0}

        with self.db_manager.get_session() as session:
            for record in batch:
                existing = (
                    session.query(GlobalPrice)
                    .filter(
                        GlobalPrice.date == record["date"],
                        GlobalPrice.commodity == record["commodity"],
                        GlobalPrice.source == record["source"],
                    )
                    .first()
                )

                if existing:
                    result["skipped"] += 1
                    continue

                session.add(
                    GlobalPrice(
                        date=record["date"],
                        commodity=record["commodity"],
                        price=record["price"],
                        currency=record["currency"],
                        unit=record["unit"],
                        region=record["region"],
                        source=record["source"],
                        indicator_code=record["indicator_code"],
                    )
                )
                result["inserted"] += 1

            session.commit()

        return result


class StandaloneFREDImporter:
    """
    Import FRED data from Foodberg's own collected data
    """

    CATEGORY_MAP = {
        "CPIUFDSL": "Food CPI",
        "CUSR0000SAF11": "Food CPI",
        "CUSR0000SEFV": "Food CPI",
        "CUSR0000SAF111": "Food CPI",
        "CUSR0000SAF112": "Food CPI",
        "CUSR0000SEFJ": "Food CPI",
        "CUSR0000SAF113": "Food CPI",
        "WPU01": "PPI",
        "WPU02": "PPI",
        "CPIAUCSL": "Inflation",
        "UNRATE": "Employment",
        "FEDFUNDS": "Interest Rates",
    }

    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            self.data_path = DEFAULT_DATA_DIR / "fred_data.json"
        else:
            self.data_path = Path(data_path)

        self.db_manager = None

    def set_database_manager(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def import_all(self, batch_size: int = 500) -> Dict[str, int]:
        """Import all FRED data"""
        if not self.db_manager:
            raise ValueError("Database manager not set")

        if not self.data_path.exists():
            raise FileNotFoundError(f"FRED data not found: {self.data_path}")

        with open(self.data_path) as f:
            data = json.load(f)

        stats = {"imported": 0, "skipped": 0, "errors": 0}

        print(f"\n{'='*60}")
        print("FRED ECONOMIC DATA IMPORT")
        print(f"Source: {self.data_path.name}")
        print(f"{'='*60}\n")

        batch = []
        for series_id, series_info in data.items():
            if "error" in series_info:
                print(f"  {series_id}: SKIPPED (error)")
                continue

            name = series_info.get("name", series_id)
            records = series_info.get("data", [])

            for record in records:
                try:
                    date_obj = datetime.strptime(record["date"], "%Y-%m-%d")

                    batch.append(
                        {
                            "date": date_obj,
                            "series_id": series_id,
                            "indicator_name": name,
                            "value": float(record["value"]),
                            "category": self.CATEGORY_MAP.get(series_id, "Other"),
                            "frequency": "Monthly",
                            "source": "FRED",
                        }
                    )

                    if len(batch) >= batch_size:
                        result = self._insert_batch(batch)
                        stats["imported"] += result["inserted"]
                        stats["skipped"] += result["skipped"]
                        batch = []

                except Exception as e:
                    stats["errors"] += 1
                    logger.warning(f"Error processing record: {e}")

            print(f"  {series_id}: {len(records)} records")

        # Insert remaining
        if batch:
            result = self._insert_batch(batch)
            stats["imported"] += result["inserted"]
            stats["skipped"] += result["skipped"]

        print(f"\n{'='*60}")
        print(
            f"Imported: {stats['imported']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}"
        )
        print(f"{'='*60}\n")

        return stats

    def _insert_batch(self, batch: List[Dict]) -> Dict[str, int]:
        result = {"inserted": 0, "skipped": 0}

        with self.db_manager.get_session() as session:
            for record in batch:
                existing = (
                    session.query(EconomicIndicator)
                    .filter(
                        EconomicIndicator.date == record["date"],
                        EconomicIndicator.series_id == record["series_id"],
                        EconomicIndicator.source == record["source"],
                    )
                    .first()
                )

                if existing:
                    result["skipped"] += 1
                    continue

                session.add(
                    EconomicIndicator(
                        date=record["date"],
                        series_id=record["series_id"],
                        indicator_name=record["indicator_name"],
                        value=record["value"],
                        category=record["category"],
                        frequency=record["frequency"],
                        source=record["source"],
                    )
                )
                result["inserted"] += 1

            session.commit()

        return result


class StandaloneWorldBankImporter:
    """
    Import World Bank agricultural indicators from Foodberg's collected data
    """

    INDICATOR_CATEGORIES = {
        "AG.PRD.FOOD.XD": "Production",
        "AG.PRD.CROP.XD": "Production",
        "AG.PRD.LVSK.XD": "Production",
        "AG.LND.AGRI.K2": "Land Use",
        "AG.LND.AGRI.ZS": "Land Use",
        "AG.LND.ARBL.ZS": "Land Use",
        "AG.CON.FERT.ZS": "Inputs",
        "FP.CPI.TOTL": "Prices",
        "SN.ITK.DEFC.ZS": "Food Security",
        "TX.VAL.FOOD.ZS.UN": "Trade",
        "TM.VAL.FOOD.ZS.UN": "Trade",
    }

    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            self.data_path = DEFAULT_DATA_DIR / "worldbank_data.json"
        else:
            self.data_path = Path(data_path)

        self.db_manager = None

    def set_database_manager(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def import_all(self, batch_size: int = 500) -> Dict[str, int]:
        """Import all World Bank data"""
        if not self.db_manager:
            raise ValueError("Database manager not set")

        if not self.data_path.exists():
            raise FileNotFoundError(f"World Bank data not found: {self.data_path}")

        with open(self.data_path) as f:
            data = json.load(f)

        stats = {"imported": 0, "skipped": 0, "errors": 0}

        print(f"\n{'='*60}")
        print("WORLD BANK AGRICULTURAL DATA IMPORT")
        print(f"Source: {self.data_path.name}")
        print(f"{'='*60}\n")

        batch = []
        for indicator_code, info in data.items():
            if "error" in info or "data" not in info:
                print(f"  {indicator_code}: Skipped (error or no data)")
                continue

            name = info.get("name", indicator_code)
            records = info.get("data", [])
            category = self.INDICATOR_CATEGORIES.get(indicator_code, "Other")

            for record in records:
                try:
                    # World Bank uses year format
                    year = int(record["date"])
                    date_obj = datetime(year, 12, 31)  # End of year

                    batch.append(
                        {
                            "date": date_obj,
                            "series_id": f"WB_{indicator_code}_{record.get('country', 'WLD')}",
                            "indicator_name": f"{name} - {record.get('country_name', 'Unknown')}",
                            "value": float(record["value"]),
                            "category": category,
                            "frequency": "Annual",
                            "source": "WorldBank",
                        }
                    )

                    if len(batch) >= batch_size:
                        result = self._insert_batch(batch)
                        stats["imported"] += result["inserted"]
                        stats["skipped"] += result["skipped"]
                        batch = []

                except Exception as e:
                    stats["errors"] += 1
                    logger.warning(f"Error processing record: {e}")

            print(f"  {indicator_code}: {len(records)} records")

        # Insert remaining
        if batch:
            result = self._insert_batch(batch)
            stats["imported"] += result["inserted"]
            stats["skipped"] += result["skipped"]

        print(f"\n{'='*60}")
        print(
            f"Imported: {stats['imported']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}"
        )
        print(f"{'='*60}\n")

        return stats

    def _insert_batch(self, batch: List[Dict]) -> Dict[str, int]:
        result = {"inserted": 0, "skipped": 0}

        with self.db_manager.get_session() as session:
            for record in batch:
                existing = (
                    session.query(EconomicIndicator)
                    .filter(
                        EconomicIndicator.date == record["date"],
                        EconomicIndicator.series_id == record["series_id"],
                        EconomicIndicator.source == record["source"],
                    )
                    .first()
                )

                if existing:
                    result["skipped"] += 1
                    continue

                session.add(
                    EconomicIndicator(
                        date=record["date"],
                        series_id=record["series_id"],
                        indicator_name=record["indicator_name"],
                        value=record["value"],
                        category=record["category"],
                        frequency=record["frequency"],
                        source=record["source"],
                    )
                )
                result["inserted"] += 1

            session.commit()

        return result


class StandaloneBLSImporter:
    """
    Import BLS data from Foodberg's own collected data
    """

    SERIES_NAMES = {
        "CUUR0000SAF": "CPI - Food and Beverages",
        "CUUR0000SAF11": "CPI - Food at Home",
        "CUUR0000SEFV": "CPI - Food Away from Home",
        "CUUR0000SAF111": "CPI - Cereals and Bakery",
        "CUUR0000SAF112": "CPI - Meats, Poultry, Fish, Eggs",
        "CUUR0000SEFJ": "CPI - Dairy",
        "CUUR0000SAF113": "CPI - Fruits and Vegetables",
    }

    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            self.data_path = DEFAULT_DATA_DIR / "bls_data.json"
        else:
            self.data_path = Path(data_path)

        self.db_manager = None

    def set_database_manager(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def import_all(self, batch_size: int = 500) -> Dict[str, int]:
        """Import all BLS data"""
        if not self.db_manager:
            raise ValueError("Database manager not set")

        if not self.data_path.exists():
            raise FileNotFoundError(f"BLS data not found: {self.data_path}")

        with open(self.data_path) as f:
            data = json.load(f)

        if "error" in data:
            raise ValueError(f"BLS data has error: {data['error']}")

        stats = {"imported": 0, "skipped": 0, "errors": 0}

        print(f"\n{'='*60}")
        print("BLS CONSUMER PRICE INDEX IMPORT")
        print(f"Source: {self.data_path.name}")
        print(f"{'='*60}\n")

        batch = []
        for series_id, series_info in data.items():
            if "error" in series_info:
                print(f"  {series_id}: SKIPPED (error)")
                continue

            name = series_info.get("name", self.SERIES_NAMES.get(series_id, series_id))
            records = series_info.get("data", [])

            for record in records:
                try:
                    date_obj = datetime.strptime(record["date"], "%Y-%m-%d")

                    batch.append(
                        {
                            "date": date_obj,
                            "series_id": series_id,
                            "indicator_name": name,
                            "value": float(record["value"]),
                            "category": "Food CPI",
                            "frequency": "Monthly",
                            "source": "BLS",
                        }
                    )

                    if len(batch) >= batch_size:
                        result = self._insert_batch(batch)
                        stats["imported"] += result["inserted"]
                        stats["skipped"] += result["skipped"]
                        batch = []

                except Exception as e:
                    stats["errors"] += 1
                    logger.warning(f"Error processing record: {e}")

            print(f"  {series_id}: {len(records)} records")

        # Insert remaining
        if batch:
            result = self._insert_batch(batch)
            stats["imported"] += result["inserted"]
            stats["skipped"] += result["skipped"]

        print(f"\n{'='*60}")
        print(
            f"Imported: {stats['imported']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}"
        )
        print(f"{'='*60}\n")

        return stats

    def _insert_batch(self, batch: List[Dict]) -> Dict[str, int]:
        result = {"inserted": 0, "skipped": 0}

        with self.db_manager.get_session() as session:
            for record in batch:
                existing = (
                    session.query(EconomicIndicator)
                    .filter(
                        EconomicIndicator.date == record["date"],
                        EconomicIndicator.series_id == record["series_id"],
                        EconomicIndicator.source == record["source"],
                    )
                    .first()
                )

                if existing:
                    result["skipped"] += 1
                    continue

                session.add(
                    EconomicIndicator(
                        date=record["date"],
                        series_id=record["series_id"],
                        indicator_name=record["indicator_name"],
                        value=record["value"],
                        category=record["category"],
                        frequency=record["frequency"],
                        source=record["source"],
                    )
                )
                result["inserted"] += 1

            session.commit()

        return result
