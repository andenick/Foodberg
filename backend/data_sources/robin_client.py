"""
Robin Client - WASDE Data Reader
Accesses WASDE agricultural data from Robin's canonical data store.
Follows Arcanum protocol: Robin as single source of truth for workspace-wide data.
"""

import json
from pathlib import Path
from typing import Optional, Dict, List
import datetime
import os


class RobinWASDEClient:
    """
    Client to access WASDE (World Agricultural Supply and Demand Estimates) data
    from the Robin Council tool's canonical data store.

    Following Arcanum protocol: All projects access centralized data from Robin,
    rather than maintaining their own copies or making direct API calls.
    """

    def __init__(self):
        # Path to Robin's canonical WASDE data store
        self.robin_data_path = Path(os.environ.get("ROBIN_DATA_DIR", "Inputs/robin")) / "DATA" / "USDA_WASDE"

        # Supported commodities (matching Robin's comprehensive WASDE collector)
        # ALL 50 WASDE COMMODITIES
        
        # Core Grains (6)
        grains = ["wheat", "corn", "rice", "barley", "oats", "sorghum"]
        
        # Oilseeds (8)
        oilseeds = ["soybeans", "cotton", "rapeseed", "canola", "sunflower",
                    "flaxseed", "safflower", "peanuts"]
        
        # Livestock - Meat (6)
        livestock_meat = ["cattle", "hogs", "chickens", "turkeys", "beef", "pork"]
        
        # Livestock - Other (5)
        livestock_other = ["sheep", "goats", "bison", "wool", "mohair"]
        
        # Dairy & Eggs (2)
        dairy = ["milk", "eggs"]
        
        # Sugar & Sweeteners (2)
        sugar = ["sugarcane", "honey"]
        
        # Specialty Grains (2)
        specialty_grains = ["rye", "millet"]
        
        # Pulses (2)
        pulses = ["lentils", "peas"]
        
        # Vegetables & Tubers (2)
        vegetables = ["potatoes", "sweet_potatoes"]
        
        # Tree Nuts (5)
        nuts = ["almonds", "walnuts", "pecans", "pistachios", "hazelnuts"]
        
        # Fruits (7)
        fruits = ["avocados", "blueberries", "strawberries", "grapes",
                  "oranges", "apples", "cranberries"]
        
        # Forage/Feed (1)
        forage = ["hay"]
        
        # Other Crops (2)
        other = ["tobacco", "mushrooms"]
        
        # Combine all (50 total)
        self.supported_commodities = (grains + oilseeds + livestock_meat + 
                                       livestock_other + dairy + sugar + 
                                       specialty_grains + pulses + vegetables + 
                                       nuts + fruits + forage + other)

        if not self.robin_data_path.exists():
            raise FileNotFoundError(
                f"Robin WASDE data directory not found: {self.robin_data_path}. "
                "Ensure Robin's nass_collector.py has been run to populate data."
            )

    def get_latest_file(self, commodity: str) -> Optional[Path]:
        """
        Find the most recent WASDE data file for a given commodity.

        Args:
            commodity: Commodity name (wheat, corn, rice, soybeans, cotton)

        Returns:
            Path to the latest data file, or None if not found
        """
        commodity = commodity.lower()

        if commodity not in self.supported_commodities:
            raise ValueError(
                f"Unsupported commodity: {commodity}. "
                f"Supported: {', '.join(self.supported_commodities)}"
            )

        # Pattern: wasde_{commodity}_YYYY-MM-DD.json
        pattern = f"wasde_{commodity}_*.json"
        files = list(self.robin_data_path.glob(pattern))

        if not files:
            return None

        # Sort by modification time (most recent first)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return files[0]

    def get_commodity_data(self, commodity: str) -> Optional[Dict]:
        """
        Retrieve the latest WASDE data for a specific commodity.

        Args:
            commodity: Commodity name (wheat, corn, rice, soybeans, cotton)

        Returns:
            Dictionary containing commodity data with metadata, or None if not found
        """
        latest_file = self.get_latest_file(commodity)

        if not latest_file:
            return None

        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Add file metadata to response
            data['file_info'] = {
                'filename': latest_file.name,
                'last_modified': datetime.datetime.fromtimestamp(
                    latest_file.stat().st_mtime
                ).isoformat(),
                'file_size_mb': round(latest_file.stat().st_size / (1024 * 1024), 2)
            }

            return data

        except Exception as e:
            print(f"Error reading WASDE data for {commodity}: {e}")
            return None

    def get_summary(self, commodity: str) -> Optional[Dict]:
        """
        Get a summary of WASDE data without the full dataset (for faster responses).

        Args:
            commodity: Commodity name

        Returns:
            Summary dictionary with metadata and sample data points
        """
        data = self.get_commodity_data(commodity)

        if not data:
            return None

        # Return metadata and a sample of data points (first 100)
        summary = {
            'commodity': data.get('commodity'),
            'source': data.get('source'),
            'retrieved_at': data.get('retrieved_at'),
            'data_points': data.get('data_points'),
            'file_info': data.get('file_info'),
            'sample_data': data.get('data', [])[:100] if data.get('data') else []
        }

        return summary

    def get_national_data(self, commodity: str) -> Optional[List[Dict]]:
        """
        Get only national-level (US TOTAL) data for a commodity.

        Args:
            commodity: Commodity name

        Returns:
            List of national-level data points
        """
        data = self.get_commodity_data(commodity)

        if not data or 'data' not in data:
            return None

        # Filter for national level data
        national_data = [
            point for point in data['data']
            if point.get('state_name') == 'US TOTAL' or
               point.get('agg_level_desc') == 'NATIONAL'
        ]

        return national_data

    def get_state_data(self, commodity: str, state: str) -> Optional[List[Dict]]:
        """
        Get data for a specific state.

        Args:
            commodity: Commodity name
            state: State name (e.g., 'KANSAS', 'CALIFORNIA')

        Returns:
            List of data points for the specified state
        """
        data = self.get_commodity_data(commodity)

        if not data or 'data' not in data:
            return None

        state = state.upper()

        # Filter for specific state
        state_data = [
            point for point in data['data']
            if point.get('state_name') == state
        ]

        return state_data

    def get_available_commodities(self) -> List[Dict]:
        """
        List all available commodities with their file information.

        Returns:
            List of dictionaries with commodity info
        """
        available = []

        for commodity in self.supported_commodities:
            latest_file = self.get_latest_file(commodity)

            if latest_file:
                available.append({
                    'commodity': commodity,
                    'filename': latest_file.name,
                    'last_updated': datetime.datetime.fromtimestamp(
                        latest_file.stat().st_mtime
                    ).isoformat(),
                    'file_size_mb': round(latest_file.stat().st_size / (1024 * 1024), 2)
                })

        return available


# Example usage
if __name__ == "__main__":
    client = RobinWASDEClient()

    # List available commodities
    print("Available WASDE commodities:")
    for commodity_info in client.get_available_commodities():
        print(f"  - {commodity_info['commodity']}: {commodity_info['file_size_mb']} MB")

    # Get summary for wheat
    wheat_summary = client.get_summary('wheat')
    if wheat_summary:
        print(f"\nWHEAT Summary:")
        print(f"  Data points: {wheat_summary['data_points']}")
        print(f"  Retrieved: {wheat_summary['retrieved_at']}")
        print(f"  File size: {wheat_summary['file_info']['file_size_mb']} MB")
