"""
FAO (Food and Agriculture Organization) API Client
Provides UN global food price indices and commodity data

Data Source: http://www.fao.org/worldfoodsituation/foodpricesindex/en/
API: https://fenixservices.fao.org/faostat/api/v1/en/ (FREE)
"""

import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

class FAOClient:
    def __init__(self):
        self.base_url = 'https://fenixservices.fao.org/faostat/api/v1/en'
        self.food_price_index_url = 'http://www.fao.org/faostat/en/#data/PP'
        
        # FAO Food Price Index categories
        self.categories = {
            'meat': 'Meat Price Index',
            'dairy': 'Dairy Price Index',
            'cereals': 'Cereal Price Index',
            'oils': 'Oils Price Index',
            'sugar': 'Sugar Price Index',
            'overall': 'FAO Food Price Index'
        }
    
    async def get_food_price_index(self, category: str = 'overall') -> Dict:
        """
        Get FAO Food Price Index data
        
        Note: FAO provides CSV/Excel downloads. For real implementation,
        we'll need to scrape or use their bulk data files.
        """
        # Placeholder: In production, fetch from FAO data portal
        # For now, return structure showing what data would look like
        
        current_month = datetime.now().strftime('%Y-%m')
        
        # Mock data structure (replace with actual FAO data)
        return {
            'category': category,
            'index_name': self.categories.get(category, 'Overall'),
            'current_index': 120.5,  # Base 2014-2016 = 100
            'previous_month': 118.3,
            'change_percent': 1.9,
            'date': current_month,
            'year_ago_index': 115.2,
            'yoy_change_percent': 4.6,
            'historical_data': self.generate_mock_historical(24)
        }
    
    def generate_mock_historical(self, months: int) -> List[Dict]:
        """Generate mock historical data (replace with real FAO data)"""
        base_index = 115
        data = []
        
        for i in range(months):
            date = datetime.now() - timedelta(days=30 * (months - i))
            index_value = base_index + (i * 0.5) + (i % 3 - 1) * 2
            
            data.append({
                'date': date.strftime('%Y-%m'),
                'index': round(index_value, 1),
                'category': 'overall'
            })
        
        return data
    
    async def get_all_indices(self) -> Dict:
        """Get all FAO food price indices"""
        indices = {}
        
        for category in self.categories.keys():
            try:
                indices[category] = await self.get_food_price_index(category)
            except Exception as e:
                indices[category] = {'error': str(e)}
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'FAO - Food and Agriculture Organization',
            'indices': indices,
            'summary': {
                'overall_index': indices.get('overall', {}).get('current_index', 0),
                'trend': self.calculate_trend(indices),
                'alert': self.generate_alert(indices)
            }
        }
    
    def calculate_trend(self, indices: Dict) -> str:
        """Calculate overall trend from indices"""
        if 'overall' in indices and 'change_percent' in indices['overall']:
            change = indices['overall']['change_percent']
            if change > 2:
                return 'strongly_increasing'
            elif change > 0.5:
                return 'increasing'
            elif change < -2:
                return 'strongly_decreasing'
            elif change < -0.5:
                return 'decreasing'
        return 'stable'
    
    def generate_alert(self, indices: Dict) -> Optional[str]:
        """Generate alert if significant price movement"""
        if 'overall' in indices:
            change = indices['overall'].get('change_percent', 0)
            if abs(change) > 3:
                direction = 'spike' if change > 0 else 'drop'
                return f"FAO Food Price Index {direction}: {abs(change):.1f}% in last month"
        return None
    
    async def export_to_excel(self, filepath: str):
        """Export FAO data to Druck-compliant Excel"""
        all_indices = await self.get_all_indices()
        
        rows = []
        for category, data in all_indices['indices'].items():
            if 'historical_data' in data:
                for point in data['historical_data']:
                    rows.append({
                        'category': category,
                        'date': point['date'],
                        'index_value': point['index'],
                        'base': '2014-2016 = 100'
                    })
        
        df = pd.DataFrame(rows)
        df.to_excel(filepath, sheet_name='FAO_Food_Price_Index', index=False)
        
        return filepath


# Example usage
if __name__ == "__main__":
    import asyncio
    from datetime import timedelta
    
    async def main():
        client = FAOClient()
        
        print("Fetching FAO Food Price Indices...")
        indices = await client.get_all_indices()
        
        print(f"\n🌍 FAO Food Price Index (Global)")
        print(f"Overall Index: {indices['summary']['overall_index']}")
        print(f"Trend: {indices['summary']['trend']}")
        if indices['summary']['alert']:
            print(f"⚠️ Alert: {indices['summary']['alert']}")
    
    asyncio.run(main())

