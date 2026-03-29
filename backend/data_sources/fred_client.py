"""
FRED (Federal Reserve Economic Data) API Client
Provides economic indicators: CPI, PPI, inflation forecasts

API Documentation: https://fred.stlouisfed.org/docs/api/
Registration: https://fred.stlouisfed.org/docs/api/api_key.html (FREE)
"""

import os
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

class FREDClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('FRED_API_KEY')
        self.base_url = 'https://api.stlouisfed.org/fred'
        
        # Economic series IDs
        self.series = {
            'food_cpi': 'CPIUFDSL',  # CPI for Food
            'food_home_cpi': 'CUSR0000SAF11',  # CPI: Food at Home
            'food_away_cpi': 'CUSR0000SEFV',  # CPI: Food Away from Home
            'ppi_farm': 'WPU01',  # PPI: Farm Products
            'ppi_food': 'WPU02',  # PPI: Processed Foods
            'inflation': 'FPCPITOTLZGUSA',  # Inflation Rate
            'unemployment': 'UNRATE',  # Unemployment Rate (affects spending)
        }
    
    async def get_series_data(
        self, 
        series_id: str, 
        start_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Fetch data for a specific economic series"""
        if not self.api_key:
            raise ValueError("FRED API key not configured")
        
        # Default to last 2 years
        if not start_date:
            start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'{self.base_url}/series/observations',
                params={
                    'series_id': series_id,
                    'api_key': self.api_key,
                    'file_type': 'json',
                    'observation_start': start_date,
                    'limit': limit,
                    'sort_order': 'desc'
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            observations = data.get('observations', [])
            return [
                {
                    'date': obs['date'],
                    'value': float(obs['value']) if obs['value'] != '.' else None,
                    'series_id': series_id
                }
                for obs in observations
                if obs['value'] != '.'
            ]
    
    async def get_food_cpi(self, months: int = 24) -> Dict:
        """Get Consumer Price Index for food"""
        data = await self.get_series_data('CPIUFDSL', limit=months)
        
        # Calculate year-over-year change
        if len(data) >= 13:
            latest = data[0]['value']
            year_ago = data[12]['value']
            yoy_change = ((latest - year_ago) / year_ago) * 100
        else:
            yoy_change = 0
        
        return {
            'indicator': 'Food CPI',
            'current_value': data[0]['value'] if data else None,
            'date': data[0]['date'] if data else None,
            'yoy_change_percent': round(yoy_change, 2),
            'trend': 'increasing' if yoy_change > 0 else 'decreasing',
            'data': data[:12]  # Last 12 months
        }
    
    async def get_ppi_food(self, months: int = 24) -> Dict:
        """Get Producer Price Index for food"""
        data = await self.get_series_data('WPU02', limit=months)
        
        if len(data) >= 13:
            latest = data[0]['value']
            year_ago = data[12]['value']
            yoy_change = ((latest - year_ago) / year_ago) * 100
        else:
            yoy_change = 0
        
        return {
            'indicator': 'Food PPI',
            'current_value': data[0]['value'] if data else None,
            'date': data[0]['date'] if data else None,
            'yoy_change_percent': round(yoy_change, 2),
            'trend': 'increasing' if yoy_change > 0 else 'decreasing',
            'data': data[:12]
        }
    
    async def get_inflation_rate(self) -> Dict:
        """Get current inflation rate"""
        data = await self.get_series_data('FPCPITOTLZGUSA', limit=12)
        
        return {
            'indicator': 'Inflation Rate',
            'current_value': data[0]['value'] if data else None,
            'date': data[0]['date'] if data else None,
            'data': data
        }
    
    async def get_all_indicators(self) -> Dict:
        """Get all economic indicators relevant to food costs"""
        try:
            food_cpi = await self.get_food_cpi()
            ppi_food = await self.get_ppi_food()
            inflation = await self.get_inflation_rate()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'indicators': {
                    'cpi_food': food_cpi,
                    'ppi_food': ppi_food,
                    'inflation': inflation
                },
                'summary': {
                    'food_inflation': food_cpi['yoy_change_percent'],
                    'producer_pressure': ppi_food['yoy_change_percent'],
                    'overall_inflation': inflation['current_value'],
                    'outlook': self.generate_outlook(food_cpi, ppi_food, inflation)
                }
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def generate_outlook(self, cpi, ppi, inflation) -> str:
        """Generate simple outlook based on indicators"""
        if ppi['yoy_change_percent'] > cpi['yoy_change_percent']:
            return "Producer prices rising faster than consumer - expect price increases"
        elif cpi['yoy_change_percent'] > 5:
            return "High food inflation - cost pressures significant"
        elif cpi['yoy_change_percent'] < 2:
            return "Stable food prices - good environment for menu planning"
        else:
            return "Moderate inflation - monitor closely"
    
    async def export_to_excel(self, filepath: str):
        """Export all indicators to Druck-compliant Excel"""
        indicators = await self.get_all_indicators()
        
        # Flatten data for Excel
        rows = []
        for name, indicator in indicators['indicators'].items():
            if 'data' in indicator:
                for point in indicator['data']:
                    rows.append({
                        'indicator': name,
                        'date': point['date'],
                        'value': point['value'],
                        'series_id': point['series_id']
                    })
        
        df = pd.DataFrame(rows)
        df.to_excel(filepath, sheet_name='Economic_Indicators', index=False)
        
        return filepath


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        client = FREDClient()
        
        print("Fetching FRED economic indicators...")
        indicators = await client.get_all_indicators()
        
        print("\n📊 Economic Indicators:")
        print(f"Food CPI: {indicators['indicators']['cpi_food']['current_value']}")
        print(f"YoY Change: {indicators['indicators']['cpi_food']['yoy_change_percent']}%")
        print(f"\nOutlook: {indicators['summary']['outlook']}")
    
    asyncio.run(main())

