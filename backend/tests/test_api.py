"""
Backend API Tests
Tests all FastAPI endpoints for correct responses

Target: 80% coverage
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)

# ==================== CORE ENDPOINTS ====================

def test_root():
    """Test API root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()['service'] == 'Foodberg API'
    assert response.json()['status'] == 'operational'

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'
    assert 'services' in response.json()

# ==================== PRICE ENDPOINTS ====================

def test_terminal_prices():
    """Test terminal market prices endpoint"""
    response = client.get("/api/prices/terminal/new_york")
    assert response.status_code == 200
    assert 'market' in response.json()
    assert 'commodities' in response.json()

def test_terminal_prices_invalid_market():
    """Test with invalid market"""
    response = client.get("/api/prices/terminal/invalid_market")
    assert response.status_code == 200  # Should still return data

def test_commodity_prices():
    """Test commodity prices across markets"""
    response = client.get("/api/prices/commodity/tomatoes")
    assert response.status_code == 200
    assert 'commodity' in response.json()
    assert 'markets' in response.json()

def test_historical_prices():
    """Test historical price data"""
    response = client.get("/api/prices/historical/chicken")
    assert response.status_code == 200
    assert 'commodity' in response.json()
    assert 'data' in response.json()

def test_historical_prices_with_params():
    """Test historical prices with custom parameters"""
    response = client.get("/api/prices/historical/beef?market=chicago&days=60")
    assert response.status_code == 200

# ==================== RECIPE ENDPOINTS ====================

def test_recipe_costing():
    """Test recipe cost calculation"""
    recipe = {
        "name": "Test Recipe",
        "yield_amount": 4,
        "ingredients": [
            {
                "name": "Chicken Breast",
                "quantity": 2,
                "unit": "lb",
                "purchasePrice": 3.99,
                "purchaseUnit": "lb",
                "yieldPercent": 0.95,
                "preparation": "grilling"
            }
        ],
        "laborMinutes": 30,
        "laborRate": 20,
        "overheadPercent": 0.30,
        "targetFoodCostPercent": 0.28
    }
    
    response = client.post("/api/recipe/cost", json=recipe)
    assert response.status_code == 200
    assert 'recipeName' in response.json()
    assert 'costs' in response.json()
    assert 'perPortion' in response.json()

def test_recipe_costing_invalid_data():
    """Test recipe costing with invalid data"""
    response = client.post("/api/recipe/cost", json={})
    assert response.status_code == 422  # Validation error

def test_menu_engineering():
    """Test menu engineering analysis"""
    menu_items = {
        "items": [
            {"id": "1", "name": "Item 1", "menuPrice": 20.0, "cost": 5.0, "profit": 15.0, "unitsSold": 100},
            {"id": "2", "name": "Item 2", "menuPrice": 15.0, "cost": 8.0, "profit": 7.0, "unitsSold": 150}
        ]
    }
    
    response = client.post("/api/recipe/menu-engineering", json=menu_items)
    assert response.status_code == 200
    assert 'items' in response.json()
    assert 'averages' in response.json()

# ==================== ALERT ENDPOINTS ====================

def test_get_price_alerts():
    """Test getting price alerts"""
    response = client.get("/api/alerts/price-changes")
    assert response.status_code == 200
    assert 'alerts' in response.json()

def test_create_price_alert():
    """Test creating price alert"""
    alert = {
        "commodity": "beef",
        "threshold": 15.0,
        "direction": "up",
        "comparison": "percent"
    }
    
    response = client.post("/api/alerts/create", json=alert)
    assert response.status_code == 200
    assert response.json()['success'] == True

# ==================== AI ENDPOINTS ====================

def test_ai_substitutions():
    """Test AI substitution endpoint"""
    data = {
        "ingredient": "tomatoes",
        "current_price": 2.45,
        "price_spike_percent": 30
    }
    
    response = client.post("/api/ai/substitutions", json=data)
    assert response.status_code == 200
    assert 'substitutions' in response.json()

def test_nutrition_data():
    """Test nutrition data retrieval"""
    response = client.get("/api/ai/nutrition/chicken")
    assert response.status_code == 200
    assert 'ingredient' in response.json()

def test_nutrition_compare():
    """Test nutrition comparison"""
    data = {
        "ingredient1": "chicken breast",
        "ingredient2": "turkey breast"
    }
    
    response = client.post("/api/ai/nutrition/compare", json=data)
    assert response.status_code == 200

# ==================== SEASONAL ENDPOINTS ====================

def test_seasonal_calendar():
    """Test seasonal calendar data"""
    response = client.get("/api/seasonal/calendar")
    assert response.status_code == 200
    assert 'month' in response.json()
    assert 'seasonal_items' in response.json()

def test_seasonal_calendar_specific_month():
    """Test seasonal calendar for specific month"""
    response = client.get("/api/seasonal/calendar?month=6")
    assert response.status_code == 200
    assert response.json()['month'] == 6

# ==================== ECONOMIC INDICATORS ====================

def test_economic_indicators():
    """Test FRED economic indicators"""
    response = client.get("/api/economic/indicators")
    assert response.status_code == 200
    # Note: May fail if FRED_API_KEY not set

def test_fao_index():
    """Test FAO food price index"""
    response = client.get("/api/global/fao-index")
    assert response.status_code == 200

def test_fao_index_category():
    """Test FAO index for specific category"""
    response = client.get("/api/global/fao-index?category=meat")
    assert response.status_code == 200

def test_worldbank_commodity():
    """Test World Bank commodity data"""
    response = client.get("/api/global/worldbank/wheat")
    assert response.status_code == 200
    assert 'commodity' in response.json()

# ==================== VENDOR ENDPOINTS ====================

def test_vendor_compare():
    """Test vendor price comparison"""
    data = {
        "commodity": "chicken",
        "vendor_data": {}
    }
    
    response = client.post("/api/vendors/compare", json=data)
    assert response.status_code == 200

# ==================== ML ENDPOINTS ====================

def test_ml_predict():
    """Test ML price prediction (may fail if no model trained)"""
    response = client.get("/api/ml/predict/chicken")
    # May return 404 if no model exists - that's acceptable
    assert response.status_code in [200, 404]

# ==================== REPORTS ENDPOINTS ====================

def test_generate_report():
    """Test report generation"""
    data = {
        "type": "weekly_summary",
        "params": {}
    }
    
    response = client.post("/api/reports/generate", json=data)
    assert response.status_code == 200
    assert 'success' in response.json()


# ==================== INTEGRATION TESTS ====================

@pytest.mark.asyncio
async def test_full_recipe_workflow():
    """Integration test: Complete recipe costing workflow"""
    # 1. Get current prices
    prices_response = client.get("/api/prices/terminal/new_york")
    assert prices_response.status_code == 200
    
    # 2. Cost a recipe
    recipe = {
        "name": "Integration Test Recipe",
        "yield_amount": 4,
        "ingredients": [
            {
                "name": "Chicken",
                "quantity": 2,
                "unit": "lb",
                "purchasePrice": 3.99,
                "purchaseUnit": "lb",
                "yieldPercent": 0.95,
                "preparation": "grilling"
            }
        ],
        "laborMinutes": 20,
        "laborRate": 20
    }
    
    cost_response = client.post("/api/recipe/cost", json=recipe)
    assert cost_response.status_code == 200
    
    # 3. Find substitutions
    sub_response = client.post("/api/ai/substitutions", json={
        "ingredient": "chicken",
        "current_price": 3.99
    })
    assert sub_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=html"])

