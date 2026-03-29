import requests
import asyncio
from pathlib import Path
import json
import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file located in the parent directory (backend/)
dotenv_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

class USDAMarketNewsClient:
    def __init__(self):
        self.base_url = 'https://mymarketnews.ams.usda.gov/api/v1.2' # Updated to v1.2
        self.api_key = os.getenv("USDA_API_KEY")
        if not self.api_key:
            raise ValueError("USDA_API_KEY not found in environment variables.")
        self.cache_dir = Path(__file__).parent.parent / 'data' / 'cache' / 'usda'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_duration = datetime.timedelta(hours=1)
        self.terminal_markets = {
            'atlanta': 'AJ_FV020',
            'boston': 'BH_FV020',
            'chicago': 'GX_FV020',
            'columbia': 'CU_FV020',
            'dallas': 'DA_FV020',
            'detroit': 'DL_FV020',
            'los_angeles': 'AJ_FV024',
            'miami': 'MH_FV020',
            'new_york': 'JO_FV020',
            'philadelphia': 'PD_FV020',
            'san_francisco': 'SF_FV020',
            'seattle': 'SE_FV020'
        }

    def _get_cached_data(self, cache_key):
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            last_modified = datetime.datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.datetime.now() - last_modified < self.cache_duration:
                with open(cache_file, 'r') as f:
                    return json.load(f)
        return None

    def _save_to_cache(self, cache_key, data):
        cache_file = self.cache_dir / f"{cache_key}.json"
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_terminal_market_prices(self, market='new_york', report_date=None):
        report_id = self.terminal_markets.get(market.lower(), self.terminal_markets['new_york'])
        date_str = report_date or datetime.date.today().isoformat()
        cache_key = f"terminal_{market}_{date_str}"

        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            print(f"Using cached data for {market} terminal market")
            return cached_data

        try:
            # According to observed patterns, the slug is used in the URL, not as a param
            url = f"{self.base_url}/reports/{report_id}"
            headers = {'x-api-key': self.api_key}
            # The API seems to filter by a single date or a date range
            params = {'report_date': date_str, 'format': 'json'} 
            
            print(f"Requesting URL: {url} with params: {params}") # DEBUGGING
            
            response = requests.get(url, params=params, headers=headers, timeout=30) # Increased timeout
            
            print(f"Response Status Code: {response.status_code}") # DEBUGGING
            
            response.raise_for_status()
            
            report_data = response.json()
            
            # Save raw response for inspection
            raw_response_path = self.cache_dir / f"raw_{cache_key}.json"
            with open(raw_response_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"Saved raw response to {raw_response_path}") # DEBUGGING

            if isinstance(report_data, list) and report_data:
                 # Assuming the first result is the most relevant
                processed_data = self._process_terminal_market_data(report_data[0])
                self._save_to_cache(cache_key, processed_data)
                return processed_data
            elif isinstance(report_data, dict) and report_data.get('results'):
                 processed_data = self._process_terminal_market_data(report_data)
                 self._save_to_cache(cache_key, processed_data)
                 return processed_data
            else:
                print(f"No results found for {market} on {date_str}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching terminal market data for {market}: {e}")
            return None

    def _process_terminal_market_data(self, raw_data):
        processed = {
            "timestamp": datetime.datetime.now().isoformat(),
            "market": raw_data.get('market_location_name', 'Unknown'),
            "reportDate": raw_data.get('report_date'),
            "commodities": {}
        }

        results = raw_data.get('results', [])
        if not isinstance(results, list):
             return processed

        for item in results:
            commodity = item.get('comm_name', 'unknown').lower()
            if commodity not in processed['commodities']:
                processed['commodities'][commodity] = []
            
            low_price = float(item.get('low_price', 0))
            high_price = float(item.get('high_price', 0))
            
            processed['commodities'][commodity].append({
                "variety": item.get('variety', 'standard'),
                "unit": item.get('unit', 'each'),
                "lowPrice": low_price,
                "highPrice": high_price,
                "avgPrice": (low_price + high_price) / 2 if high_price > 0 else low_price,
                "origin": item.get('origin', 'Unknown'),
            })
        return processed

if __name__ == '__main__':
    client = USDAMarketNewsClient()
    print("Fetching New York terminal market prices...")
    ny_prices = client.get_terminal_market_prices('new_york')
    if ny_prices and ny_prices.get('commodities'):
        print('Available commodities:', list(ny_prices['commodities'].keys())[:10])
    else:
        print("Could not retrieve data.")
