"""
API Ninja Client for Food Data
Provides nutritional information and food data enrichment

API Documentation: https://api-ninjas.com/api/nutrition
Registration: https://api-ninjas.com/register (FREE - 10K requests/month)
"""

import os
import httpx
from typing import List, Dict, Optional

class APINinjaClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('API_NINJA_KEY')
        self.base_url = 'https://api.api-ninjas.com/v1'
    
    async def get_nutrition(self, ingredient: str) -> Dict:
        """Get nutritional information for an ingredient"""
        if not self.api_key:
            return {'error': 'API Ninja key not configured'}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f'{self.base_url}/nutrition',
                    params={'query': ingredient},
                    headers={'X-Api-Key': self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    return {'error': f'No nutrition data found for {ingredient}'}
                
                # Return first match
                nutrition = data[0]
                return {
                    'name': nutrition.get('name'),
                    'calories': nutrition.get('calories'),
                    'protein_g': nutrition.get('protein_g'),
                    'fat_total_g': nutrition.get('fat_total_g'),
                    'carbohydrates_g': nutrition.get('carbohydrates_total_g'),
                    'fiber_g': nutrition.get('fiber_g'),
                    'sugar_g': nutrition.get('sugar_g'),
                    'sodium_mg': nutrition.get('sodium_mg'),
                    'serving_size_g': nutrition.get('serving_size_g', 100)
                }
            except Exception as e:
                return {'error': str(e)}
    
    async def compare_nutrition(
        self, 
        ingredient1: str, 
        ingredient2: str
    ) -> Dict:
        """Compare nutritional profiles of two ingredients"""
        n1 = await self.get_nutrition(ingredient1)
        n2 = await self.get_nutrition(ingredient2)
        
        if 'error' in n1 or 'error' in n2:
            return {'error': 'Could not fetch nutrition data'}
        
        # Calculate similarity score (0-1)
        similarity = self.calculate_nutrition_similarity(n1, n2)
        
        return {
            'ingredient1': ingredient1,
            'ingredient2': ingredient2,
            'nutrition1': n1,
            'nutrition2': n2,
            'similarity_score': similarity,
            'comparison': {
                'calories_diff_percent': self.percent_diff(n1['calories'], n2['calories']),
                'protein_diff_percent': self.percent_diff(n1['protein_g'], n2['protein_g']),
                'fat_diff_percent': self.percent_diff(n1['fat_total_g'], n2['fat_total_g']),
                'carbs_diff_percent': self.percent_diff(n1['carbohydrates_g'], n2['carbohydrates_g'])
            },
            'recommendation': self.generate_substitution_recommendation(similarity)
        }
    
    def calculate_nutrition_similarity(self, n1: Dict, n2: Dict) -> float:
        """Calculate nutritional similarity (0-1 scale)"""
        # Weight different nutrients
        weights = {
            'calories': 0.3,
            'protein_g': 0.25,
            'fat_total_g': 0.2,
            'carbohydrates_g': 0.15,
            'fiber_g': 0.1
        }
        
        total_similarity = 0
        total_weight = 0
        
        for nutrient, weight in weights.items():
            if nutrient in n1 and nutrient in n2:
                v1 = n1[nutrient]
                v2 = n2[nutrient]
                
                if v1 and v2:
                    # Calculate similarity (closer to 1 = more similar)
                    diff = abs(v1 - v2) / max(v1, v2)
                    similarity = 1 - min(diff, 1)
                    
                    total_similarity += similarity * weight
                    total_weight += weight
        
        return round(total_similarity / total_weight if total_weight > 0 else 0, 2)
    
    def percent_diff(self, v1: float, v2: float) -> float:
        """Calculate percentage difference"""
        if not v1 or not v2:
            return 0
        return round(((v2 - v1) / v1) * 100, 1)
    
    def generate_substitution_recommendation(self, similarity: float) -> str:
        """Generate recommendation based on similarity score"""
        if similarity >= 0.85:
            return "Excellent substitute - nutritionally very similar"
        elif similarity >= 0.70:
            return "Good substitute - reasonable nutritional match"
        elif similarity >= 0.50:
            return "Fair substitute - some nutritional differences"
        else:
            return "Poor substitute - significant nutritional differences"
    
    async def batch_nutrition_lookup(
        self, 
        ingredients: List[str]
    ) -> Dict[str, Dict]:
        """Get nutrition data for multiple ingredients"""
        results = {}
        
        for ingredient in ingredients:
            results[ingredient] = await self.get_nutrition(ingredient)
            # Rate limiting (10K requests/month = ~6.9 req/min max)
            await asyncio.sleep(0.2)  # 5 req/sec = well under limit
        
        return results


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        client = APINinjaClient()
        
        print("Testing API Ninja nutrition lookup...")
        
        # Get nutrition for chicken
        chicken = await client.get_nutrition('chicken breast')
        print(f"\n🍗 Chicken Breast (100g):")
        print(f"Calories: {chicken.get('calories')} kcal")
        print(f"Protein: {chicken.get('protein_g')} g")
        
        # Compare chicken vs turkey
        comparison = await client.compare_nutrition('chicken breast', 'turkey breast')
        print(f"\n🔄 Chicken vs Turkey:")
        print(f"Similarity Score: {comparison['similarity_score']}")
        print(f"Recommendation: {comparison['recommendation']}")
    
    asyncio.run(main())

