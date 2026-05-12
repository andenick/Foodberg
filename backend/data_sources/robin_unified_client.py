"""
Robin Unified Data Client
Unified access to ALL Robin data sources for Foodberg.

This client follows Arcanum protocol: Robin is the single source of truth
for all economic and agricultural data across the workspace.

Data Sources Accessed:
- USDA WASDE/NASS: Agricultural supply/demand (50 commodities)
- FRED: Economic indicators (CPI, PPI, inflation)
- BLS: Consumer/Producer Price Indices, labor statistics
- IMF: International price indices
- OECD: Purchasing power parity data
- World Bank: Global commodity prices
- USDA FoodData Central: Nutritional information
- FAO: Food Price Index (when available)
"""

import json
import sqlite3
import csv
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timedelta
import os


class RobinUnifiedClient:
    """
    Unified client for accessing all Robin data sources.

    Provides a single interface to:
    - WASDE agricultural data
    - FRED economic indicators
    - BLS price indices
    - World Bank/IMF global data
    - USDA FoodData Central nutrition data
    """

    # Base path to Robin's data store
    ROBIN_BASE = Path(os.environ.get("ROBIN_DATA_DIR", "Inputs/robin"))

    def __init__(self):
        """Initialize the unified Robin client."""
        self.data_paths = {
            "wasde": self.ROBIN_BASE / "DATA" / "USDA_WASDE",
            "fred": self.ROBIN_BASE / "DATA" / "FRED",
            "fred_db": self.ROBIN_BASE / "DATA" / "FRED" / "fred_data" / "fred_data.db",
            "bls": self.ROBIN_BASE / "DATA" / "BLS",
            "bls_prices": self.ROBIN_BASE / "DATA" / "BLS" / "prices",
            "imf": self.ROBIN_BASE / "DATA" / "IMF",
            "oecd": self.ROBIN_BASE / "DATA" / "OECD",
            "worldbank": self.ROBIN_BASE / "DATA" / "WorldBank",
            "fdc": self.ROBIN_BASE / "DATA" / "USDA_FoodDataCentral",
            "fao": self.ROBIN_BASE / "DATA" / "FAO",  # To be created
        }

        # WASDE supported commodities (50 total)
        self.wasde_commodities = self._get_wasde_commodities()

        # FRED series relevant to food prices
        self.fred_food_series = {
            "CPIUFDSL": "CPI for Food",
            "CUSR0000SAF11": "CPI: Food at Home",
            "CUSR0000SEFV": "CPI: Food Away from Home",
            "WPU01": "PPI: Farm Products",
            "WPU02": "PPI: Processed Foods",
            "FPCPITOTLZGUSA": "Inflation Rate",
            "APU0000703112": "Average Price: Eggs (dozen)",
            "APU0000703111": "Average Price: Milk (gallon)",
            "APU0000FC1101": "Average Price: Bread (lb)",
        }

        # BLS food-related series
        self.bls_food_series = {
            "CUUR0000SAF": "CPI: Food and Beverages",
            "CUUR0000SAF1": "CPI: Food",
            "CUUR0000SAF11": "CPI: Food at Home",
            "CUUR0000SAF111": "CPI: Cereals and Bakery",
            "CUUR0000SAF112": "CPI: Meats, Poultry, Fish, Eggs",
            "CUUR0000SAF113": "CPI: Dairy and Related",
            "CUUR0000SAF114": "CPI: Fruits and Vegetables",
            "CUUR0000SAF115": "CPI: Nonalcoholic Beverages",
            "CUUR0000SAF116": "CPI: Other Food at Home",
            "CUUR0000SEFV": "CPI: Food Away from Home",
        }

        self._validate_paths()

    def _validate_paths(self):
        """Check which data paths exist and log status."""
        self.available_sources = {}
        for name, path in self.data_paths.items():
            exists = path.exists()
            self.available_sources[name] = exists
            if not exists and name not in ["fao"]:  # FAO to be created
                print(f"[Robin] Warning: {name} data path not found: {path}")

    def _get_wasde_commodities(self) -> List[str]:
        """Get list of all WASDE commodities."""
        grains = ["wheat", "corn", "rice", "barley", "oats", "sorghum"]
        oilseeds = [
            "soybeans",
            "cotton",
            "rapeseed",
            "canola",
            "sunflower",
            "flaxseed",
            "safflower",
            "peanuts",
        ]
        livestock_meat = ["cattle", "hogs", "chickens", "turkeys", "beef", "pork"]
        livestock_other = ["sheep", "goats", "bison", "wool", "mohair"]
        dairy = ["milk", "eggs"]
        sugar = ["sugarcane", "honey"]
        specialty_grains = ["rye", "millet"]
        pulses = ["lentils", "peas"]
        vegetables = ["potatoes", "sweet_potatoes"]
        nuts = ["almonds", "walnuts", "pecans", "pistachios", "hazelnuts"]
        fruits = [
            "avocados",
            "blueberries",
            "strawberries",
            "grapes",
            "oranges",
            "apples",
            "cranberries",
        ]
        forage = ["hay"]
        other = ["tobacco", "mushrooms"]

        return (
            grains
            + oilseeds
            + livestock_meat
            + livestock_other
            + dairy
            + sugar
            + specialty_grains
            + pulses
            + vegetables
            + nuts
            + fruits
            + forage
            + other
        )

    # ==================== WASDE DATA ====================

    def get_wasde_commodities(self) -> List[Dict]:
        """List all available WASDE commodities with file info."""
        if not self.available_sources.get("wasde"):
            return []

        available = []
        for commodity in self.wasde_commodities:
            pattern = f"wasde_{commodity}_*.json"
            files = list(self.data_paths["wasde"].glob(pattern))
            if files:
                latest = max(files, key=lambda f: f.stat().st_mtime)
                available.append(
                    {
                        "commodity": commodity,
                        "filename": latest.name,
                        "last_updated": datetime.fromtimestamp(
                            latest.stat().st_mtime
                        ).isoformat(),
                        "file_size_mb": round(latest.stat().st_size / (1024 * 1024), 2),
                    }
                )
        return available

    def get_wasde_data(self, commodity: str) -> Optional[Dict]:
        """Get WASDE data for a specific commodity."""
        if not self.available_sources.get("wasde"):
            return None

        commodity = commodity.lower()
        pattern = f"wasde_{commodity}_*.json"
        files = list(self.data_paths["wasde"].glob(pattern))

        if not files:
            return None

        latest = max(files, key=lambda f: f.stat().st_mtime)

        try:
            with open(latest, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["_source"] = "robin_wasde"
            data["_file"] = str(latest)
            return data
        except Exception as e:
            print(f"[Robin] Error reading WASDE {commodity}: {e}")
            return None

    def get_wasde_prices(self, commodity: str) -> List[Dict]:
        """Extract price-specific data from WASDE for a commodity."""
        data = self.get_wasde_data(commodity)
        if not data or "data" not in data:
            return []

        # Filter for price-related statistics
        price_data = [
            point
            for point in data["data"]
            if "PRICE" in point.get("statisticcat_desc", "").upper()
            or "PRICE" in point.get("short_desc", "").upper()
        ]

        return price_data

    # ==================== FRED DATA ====================

    def get_fred_series(self, series_id: str, limit: int = 100) -> List[Dict]:
        """
        Get FRED time series data from Robin's FRED database.

        Args:
            series_id: FRED series ID (e.g., 'CPIUFDSL')
            limit: Maximum number of observations to return

        Returns:
            List of observations with date and value
        """
        db_path = self.data_paths["fred_db"]
        if not db_path.exists():
            print(f"[Robin] FRED database not found: {db_path}")
            return []

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Query the FRED data (table structure may vary)
            # Try common table names
            for table in ["observations", "fred_data", "series_data"]:
                try:
                    cursor.execute(
                        f"""
                        SELECT date, value
                        FROM {table}
                        WHERE series_id = ?
                        ORDER BY date DESC
                        LIMIT ?
                    """,
                        (series_id, limit),
                    )
                    rows = cursor.fetchall()
                    if rows:
                        conn.close()
                        return [
                            {"date": row[0], "value": row[1], "series_id": series_id}
                            for row in rows
                        ]
                except sqlite3.OperationalError:
                    continue

            conn.close()
            return []

        except Exception as e:
            print(f"[Robin] Error querying FRED database: {e}")
            return []

    def get_fred_food_indicators(self) -> Dict[str, List[Dict]]:
        """Get all food-related FRED indicators."""
        results = {}
        for series_id, name in self.fred_food_series.items():
            data = self.get_fred_series(series_id)
            if data:
                results[series_id] = {"name": name, "data": data}
        return results

    # ==================== BLS DATA ====================

    def get_bls_prices(self, category: str = "cu") -> List[Dict]:
        """
        Get BLS price data from Robin's BLS data store.

        Args:
            category: 'cu' for CPI, 'wp' for PPI, 'ip' for import prices

        Returns:
            List of price observations
        """
        bls_path = self.data_paths["bls_prices"] / category
        if not bls_path.exists():
            return []

        all_data = []
        for file in bls_path.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    elif isinstance(data, dict) and "data" in data:
                        all_data.extend(data["data"])
            except Exception as e:
                print(f"[Robin] Error reading BLS file {file}: {e}")

        return all_data

    def get_bls_food_cpi(self) -> Dict[str, Any]:
        """Get food-specific CPI data from BLS."""
        # Try to read from BLS collection summary
        summary_files = list(self.data_paths["bls"].glob("*collection_summary*.json"))
        if summary_files:
            try:
                with open(summary_files[0], "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Robin] Error reading BLS summary: {e}")

        return {"error": "BLS food CPI data not found"}

    # ==================== WORLD BANK DATA ====================

    def get_worldbank_commodities(self) -> List[Dict]:
        """Get World Bank commodity price data."""
        wb_path = self.data_paths["worldbank"] / "WDI_CSV"
        if not wb_path.exists():
            return []

        commodities = []
        for csv_file in wb_path.glob("*.csv"):
            try:
                with open(csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Filter for food/agriculture related indicators
                        indicator = row.get("Indicator Name", "").lower()
                        if any(
                            term in indicator
                            for term in [
                                "food",
                                "agriculture",
                                "cereal",
                                "meat",
                                "dairy",
                                "commodity",
                                "price",
                                "crop",
                            ]
                        ):
                            commodities.append(row)
            except Exception as e:
                print(f"[Robin] Error reading World Bank file {csv_file}: {e}")

        return commodities[:1000]  # Limit to first 1000 matches

    # ==================== IMF DATA ====================

    def get_imf_prices(self) -> List[Dict]:
        """Get IMF price/CPI data."""
        imf_prices = self.data_paths["imf"] / "prices" / "cpi"
        if not imf_prices.exists():
            return []

        all_data = []
        for file in imf_prices.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    elif isinstance(data, dict):
                        all_data.append(data)
            except Exception as e:
                print(f"[Robin] Error reading IMF file {file}: {e}")

        return all_data

    # ==================== USDA FOODDATA CENTRAL ====================

    def get_nutrition_data(self, food_name: str) -> Optional[Dict]:
        """Get nutritional data for a food item."""
        fdc_path = self.data_paths["fdc"]
        if not fdc_path.exists():
            return None

        # Search for matching file
        food_lower = food_name.lower().replace(" ", "_")
        for file in fdc_path.glob(f"fdc_*{food_lower}*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Robin] Error reading FDC file {file}: {e}")

        return None

    def get_available_nutrition(self) -> List[str]:
        """List all available nutrition data files."""
        fdc_path = self.data_paths["fdc"]
        if not fdc_path.exists():
            return []

        return [f.stem.replace("fdc_", "") for f in fdc_path.glob("fdc_*.json")]

    # ==================== FAO DATA (TO BE IMPLEMENTED) ====================

    def get_fao_price_index(self) -> Optional[Dict]:
        """
        Get FAO Food Price Index data.

        Note: This requires downloading the FAO CSV first.
        See: https://www.fao.org/worldfoodsituation/foodpricesindex/en/
        """
        fao_path = self.data_paths["fao"]
        if not fao_path.exists():
            return {
                "error": "FAO data not yet downloaded",
                "instructions": "Download from https://www.fao.org/worldfoodsituation/foodpricesindex/en/",
                "target_path": str(fao_path),
            }

        # Look for FAO data files
        for file in fao_path.glob("*.csv"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    return {"data": list(reader), "source": file.name}
            except Exception as e:
                print(f"[Robin] Error reading FAO file {file}: {e}")

        return None

    # ==================== UNIFIED QUERIES ====================

    def get_all_sources_status(self) -> Dict[str, Dict]:
        """Get status of all Robin data sources."""
        status = {}
        for name, available in self.available_sources.items():
            path = self.data_paths[name]
            if available:
                if path.is_file():
                    file_count = 1
                    size_mb = path.stat().st_size / (1024 * 1024)
                else:
                    files = list(path.glob("**/*"))
                    file_count = len([f for f in files if f.is_file()])
                    size_mb = sum(f.stat().st_size for f in files if f.is_file()) / (
                        1024 * 1024
                    )

                status[name] = {
                    "available": True,
                    "path": str(path),
                    "file_count": file_count,
                    "size_mb": round(size_mb, 2),
                }
            else:
                status[name] = {"available": False, "path": str(path)}

        return status

    def get_commodity_from_all_sources(self, commodity: str) -> Dict[str, Any]:
        """
        Get data for a commodity from all available sources.

        Returns aggregated data from WASDE, FRED, BLS, World Bank, etc.
        """
        commodity = commodity.lower()
        results = {
            "commodity": commodity,
            "timestamp": datetime.utcnow().isoformat(),
            "sources": {},
        }

        # WASDE data
        wasde = self.get_wasde_prices(commodity)
        if wasde:
            results["sources"]["wasde"] = {
                "record_count": len(wasde),
                "sample": wasde[:10],
            }

        # For common commodities, check FRED
        commodity_fred_map = {
            "eggs": "APU0000703112",
            "milk": "APU0000703111",
            "bread": "APU0000FC1101",
        }
        if commodity in commodity_fred_map:
            fred_data = self.get_fred_series(commodity_fred_map[commodity])
            if fred_data:
                results["sources"]["fred"] = {
                    "record_count": len(fred_data),
                    "data": fred_data[:20],
                }

        return results

    def search_all_sources(self, query: str) -> Dict[str, List[Dict]]:
        """Search for a term across all Robin data sources."""
        query = query.lower()
        results = {}

        # Search WASDE commodities
        matching_wasde = [c for c in self.wasde_commodities if query in c]
        if matching_wasde:
            results["wasde"] = [{"commodity": c} for c in matching_wasde]

        # Search FRED series
        matching_fred = [
            {"series_id": sid, "name": name}
            for sid, name in self.fred_food_series.items()
            if query in name.lower() or query in sid.lower()
        ]
        if matching_fred:
            results["fred"] = matching_fred

        # Search BLS series
        matching_bls = [
            {"series_id": sid, "name": name}
            for sid, name in self.bls_food_series.items()
            if query in name.lower() or query in sid.lower()
        ]
        if matching_bls:
            results["bls"] = matching_bls

        return results


# Convenience function for backward compatibility
def get_robin_client() -> RobinUnifiedClient:
    """Get a singleton instance of the Robin unified client."""
    return RobinUnifiedClient()


# Example usage
if __name__ == "__main__":
    client = RobinUnifiedClient()

    print("=" * 60)
    print("ROBIN UNIFIED CLIENT - DATA SOURCE STATUS")
    print("=" * 60)

    status = client.get_all_sources_status()
    for source, info in status.items():
        if info["available"]:
            print(f"✅ {source}: {info['file_count']} files, {info['size_mb']} MB")
        else:
            print(f"❌ {source}: Not available")

    print("\n" + "=" * 60)
    print("WASDE COMMODITIES")
    print("=" * 60)

    commodities = client.get_wasde_commodities()
    print(f"Found {len(commodities)} commodities")
    for c in commodities[:5]:
        print(f"  - {c['commodity']}: {c['file_size_mb']} MB")

    print("\n" + "=" * 60)
    print("FRED FOOD SERIES")
    print("=" * 60)

    for series_id, name in client.fred_food_series.items():
        data = client.get_fred_series(series_id, limit=1)
        if data:
            print(f"  ✅ {series_id}: {name} - Latest: {data[0]}")
        else:
            print(f"  ⚠️  {series_id}: {name} - No data")
