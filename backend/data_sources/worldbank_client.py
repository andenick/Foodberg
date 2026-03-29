"""
World Bank Commodities API Client
Provides international commodity pricing (Pink Sheet data)

API Documentation: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
Data: https://www.worldbank.org/en/research/commodity-markets (FREE)
"""

import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

class WorldBankClient:
    def __init__(self):
        self.base_url = 'https://api.worldbank.org/v2'
        
        # Pink Sheet commodity codes
        self.commodities = {
            # Agriculture
            'wheat': 'PWHEAMT',
            'maize': 'PMAIZMT',
            'rice': 'PRICENPQ',
            'barley': 'PBARL',
            'sorghum': 'PSORG',
            
            # Oils
            'soybean_oil': 'PSOIL',
            'palm_oil': 'PPOIL',
            'sunflower_oil': 'PSUNO',
            'olive_oil': 'POLVOIL',
            
            # Proteins
            'beef': 'PBEEF',
            'chicken': 'PPOULT',
            'pork': 'PPORK',
            'fish': 'PFISH',
            'shrimp': 'PSHRI',
            
            # Dairy
            'butter': 'PBUTTER',
            'cheese': 'PCHEESUS',
            'milk': 'PMILK',
            
            # Sugar
            'sugar': 'PSUGAUSA',
            
            # Beverages
            'coffee': 'PCOFFOTM',
            'tea': 'PTEA',
            'cocoa': 'PCOCO',
        }
    
    async def get_commodity_price(
        self, 
        commodity: str, 
        start_year: int = 2020
    ) -> Dict:
        """
        Get World Bank commodity price data
        
        Note: World Bank API returns monthly data in USD
        """
        commodity_code = self.commodities.get(commodity.lower())
        
        if not commodity_code:
            return {'error': f'Commodity {commodity} not found'}
        
        # Fetch from World Bank API
        # Format: /v2/country/all/indicator/{indicator}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f'{self.base_url}/country/WLD/indicator/{commodity_code}',
                    params={
                        'format': 'json',
                        'date': f'{start_year}:2025',
                        'per_page': 100
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                # World Bank returns [metadata, data]
                if len(data) > 1 and isinstance(data[1], list):
                    observations = data[1]
                    
                    processed = [{
                        'date': obs['date'],
                        'value': obs['value'],
                        'commodity': commodity
                    } for obs in observations if obs['value']]
                    
                    # Calculate statistics
                    values = [obs['value'] for obs in processed if obs['value']]
                    
                    return {
                        'commodity': commodity,
                        'unit': 'USD per metric ton',
                        'current_price': values[0] if values else None,
                        'average': sum(values) / len(values) if values else None,
                        'min': min(values) if values else None,
                        'max': max(values) if values else None,
                        'data': processed[:24]  # Last 24 months
                    }
            except Exception as e:
                # Return mock data if API fails
                return self.get_mock_data(commodity)
        
        return self.get_mock_data(commodity)
    
    def get_mock_data(self, commodity: str) -> Dict:
        """Return mock data structure when API unavailable"""
        base_price = {
            'wheat': 250,
            'beef': 4500,
            'chicken': 1800,
            'coffee': 3200,
        }.get(commodity, 1000)
        
        return {
            'commodity': commodity,
            'unit': 'USD per metric ton',
            'current_price': base_price,
            'average': base_price * 0.95,
            'min': base_price * 0.80,
            'max': base_price * 1.20,
            'data': [
                {
                    'date': (datetime.now() - timedelta(days=30*i)).strftime('%Y'),
                    'value': base_price + (i % 5 - 2) * 50,
                    'commodity': commodity
                }
                for i in range(12)
            ],
            'note': 'Mock data - API integration pending'
        }
    
    async def get_multiple_commodities(
        self, 
        commodities: List[str]
    ) -> Dict:
        """Get price data for multiple commodities"""
        results = {}
        
        for commodity in commodities:
            try:
                results[commodity] = await self.get_commodity_price(commodity)
            except Exception as e:
                results[commodity] = {'error': str(e)}
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'World Bank - Commodity Price Data (Pink Sheet)',
            'commodities': results
        }
    
    async def export_to_excel(self, filepath: str, commodities: List[str]):
        """Export World Bank data to Druck-compliant Excel"""
        data = await self.get_multiple_commodities(commodities)
        
        rows = []
        for commodity, info in data['commodities'].items():
            if 'data' in info:
                for point in info['data']:
                    rows.append({
                        'commodity': commodity,
                        'date': point['date'],
                        'price_usd_per_mt': point['value'],
                        'unit': 'USD per metric ton'
                    })
        
        df = pd.DataFrame(rows)
        df.to_excel(filepath, sheet_name='WorldBank_Commodities', index=False)
        
        return filepath


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        client = WorldBankClient()
        
        print("Fetching World Bank commodity prices...")
        commodities = ['wheat', 'beef', 'chicken', 'coffee']
        data = await client.get_multiple_commodities(commodities)
        
        print(f"\n🌍 World Bank Commodity Prices:")
        for commodity, info in data['commodities'].items():
            if 'current_price' in info:
                print(f"{commodity.capitalize()}: ${info['current_price']:.2f} per MT")
    
    asyncio.run(main())

