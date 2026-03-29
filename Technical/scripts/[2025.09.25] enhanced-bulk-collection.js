#!/usr/bin/env node

/**
 * Enhanced Bulk Data Collection for Foodberg
 * Explores all available USDA endpoints and additional free sources
 */

const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');

class EnhancedDataCollector {
  constructor() {
    this.SERVER_BASE_URL = 'http://localhost:3001';
    this.dataDir = path.join(__dirname, '..', 'data', 'enhanced');
    this.results = {
      timestamp: new Date().toISOString(),
      total_attempts: 0,
      successful: 0,
      failed: 0,
      new_commodities: [],
      sources_explored: [],
      results: []
    };

    // Comprehensive list of potential food commodities
    this.allCommodities = [
      // Current working items
      'wheat', 'corn', 'rice', 'oats', 'barley', 'flour', 'chicken', 'chicken-breast',
      'beef-brisket', 'pork', 'pork-loin', 'turkey', 'eggs', 'salmon', 'tuna', 'shrimp',
      'lobster', 'soybeans', 'milk', 'butter', 'cheese', 'whey', 'olive-oil', 'canola-oil',
      'vegetable-oil', 'sunflower-oil', 'tomatoes', 'tomato', 'potatoes', 'potato',
      'onions', 'onion', 'carrots', 'carrot', 'lettuce', 'spinach', 'cabbage', 'celery',

      // Expanded list - meats & proteins
      'beef', 'ground-beef', 'ribeye', 'sirloin', 't-bone', 'filet-mignon',
      'pork-chops', 'bacon', 'ham', 'sausage', 'lamb', 'goat', 'duck', 'goose',
      'chicken-thigh', 'chicken-wing', 'chicken-drumstick',
      'tilapia', 'cod', 'halibut', 'mahi-mahi', 'snapper', 'catfish', 'mackerel',
      'crab', 'oyster', 'mussel', 'scallop', 'squid', 'octopus',

      // Dairy expanded
      'cream', 'yogurt', 'sour-cream', 'cottage-cheese', 'mozzarella', 'cheddar',
      'swiss-cheese', 'parmesan', 'blue-cheese', 'goat-cheese', 'ricotta',

      // Vegetables expanded
      'broccoli', 'cauliflower', 'brussels-sprouts', 'asparagus', 'artichoke',
      'eggplant', 'zucchini', 'squash', 'cucumber', 'bell-pepper', 'jalapeno',
      'serrano', 'habanero', 'poblano', 'sweet-potato', 'yam', 'beet',
      'radish', 'turnip', 'parsnip', 'leek', 'shallot', 'scallion',
      'mushroom', 'shiitake', 'portobello', 'button-mushroom', 'oyster-mushroom',
      'kale', 'chard', 'collard', 'arugula', 'watercress', 'endive',

      // Fruits expanded
      'apple', 'banana', 'orange', 'lemon', 'lime', 'grapefruit', 'tangerine',
      'strawberry', 'blueberry', 'raspberry', 'blackberry', 'cranberry',
      'grape', 'cherry', 'peach', 'apricot', 'plum', 'nectarine', 'pear',
      'pineapple', 'mango', 'papaya', 'kiwi', 'avocado', 'pomegranate',
      'cantaloupe', 'honeydew', 'watermelon', 'fig', 'date', 'raisin',

      // Grains expanded
      'quinoa', 'buckwheat', 'millet', 'amaranth', 'bulgur', 'couscous',
      'wild-rice', 'brown-rice', 'jasmine-rice', 'basmati-rice',
      'whole-wheat', 'rye', 'spelt', 'kamut', 'farro',

      // Nuts & seeds expanded
      'almond', 'walnut', 'pecan', 'pistachio', 'cashew', 'brazil-nut',
      'hazelnut', 'macadamia', 'pine-nut', 'chestnut',
      'sunflower-seed', 'pumpkin-seed', 'sesame-seed', 'flax-seed',
      'chia-seed', 'hemp-seed', 'poppy-seed',

      // Herbs & spices expanded
      'basil', 'cilantro', 'parsley', 'dill', 'mint', 'oregano', 'thyme',
      'rosemary', 'sage', 'tarragon', 'chives', 'bay-leaf',
      'garlic', 'ginger', 'turmeric', 'cumin', 'coriander', 'fennel',
      'cardamom', 'cinnamon', 'cloves', 'nutmeg', 'allspice', 'star-anise',
      'pepper', 'black-pepper', 'white-pepper', 'cayenne', 'paprika',
      'chili-powder', 'curry-powder', 'garam-masala',
      'salt', 'sea-salt', 'kosher-salt', 'himalayan-salt',
      'saffron', 'vanilla', 'anise', 'mustard-seed',

      // Oils expanded
      'coconut-oil', 'avocado-oil', 'sesame-oil', 'walnut-oil',
      'grapeseed-oil', 'flax-oil', 'hemp-oil', 'macadamia-oil',

      // Pantry items
      'honey', 'maple-syrup', 'agave', 'molasses', 'brown-sugar',
      'sugar', 'sugar-white', 'powdered-sugar',
      'baking-soda', 'baking-powder', 'yeast', 'cornstarch',
      'arrowroot', 'tapioca', 'gelatin', 'agar',
      'vinegar', 'balsamic-vinegar', 'apple-cider-vinegar',
      'white-wine-vinegar', 'red-wine-vinegar',

      // Beverages
      'coffee', 'tea', 'green-tea', 'black-tea', 'herbal-tea',
      'cocoa', 'chocolate', 'dark-chocolate', 'milk-chocolate',

      // Specialty items
      'truffle', 'caviar', 'foie-gras', 'prosciutto', 'pancetta',
      'kimchi', 'miso', 'soy-sauce', 'fish-sauce', 'oyster-sauce',
      'tahini', 'peanut-butter', 'almond-butter', 'coconut-milk'
    ];
  }

  async initialize() {
    try {
      await fs.mkdir(this.dataDir, { recursive: true });
      console.log(`📁 Enhanced data directory: ${this.dataDir}`);
    } catch (error) {
      console.error('Failed to create data directory:', error.message);
    }
  }

  async testCommodity(commodity) {
    try {
      const response = await axios.get(`${this.SERVER_BASE_URL}/api/prices/${commodity}`, {
        timeout: 5000
      });

      if (response.ok || response.status === 200) {
        return { success: true, data: response.data };
      } else {
        return { success: false, error: `HTTP ${response.status}` };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async exploreBulkCommodities() {
    console.log(`🔍 Testing ${this.allCommodities.length} potential commodities...`);

    const batchSize = 10;
    let foundItems = [];
    let processedCount = 0;

    for (let i = 0; i < this.allCommodities.length; i += batchSize) {
      const batch = this.allCommodities.slice(i, i + batchSize);
      console.log(`\n📦 Processing batch ${Math.floor(i/batchSize) + 1}/${Math.ceil(this.allCommodities.length/batchSize)}: ${batch.join(', ')}`);

      const promises = batch.map(async (commodity) => {
        const result = await this.testCommodity(commodity);
        this.results.total_attempts++;

        if (result.success) {
          console.log(`   ✅ ${commodity}: Found data`);
          this.results.successful++;
          foundItems.push({
            commodity,
            data: result.data,
            source: 'server_endpoint'
          });
          return { commodity, found: true, data: result.data };
        } else {
          console.log(`   ❌ ${commodity}: ${result.error}`);
          this.results.failed++;
          return { commodity, found: false, error: result.error };
        }
      });

      const batchResults = await Promise.all(promises);
      this.results.results.push(...batchResults);

      processedCount += batch.length;
      console.log(`   Progress: ${processedCount}/${this.allCommodities.length} (${(processedCount/this.allCommodities.length*100).toFixed(1)}%)`);

      // Small delay to be respectful
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    return foundItems;
  }

  async exploreUSDAEndpoints() {
    console.log(`\n🏛️ Exploring additional USDA endpoints...`);

    // Attempt to discover more USDA data through different endpoints
    const usdaEndpoints = [
      '/api/usda/market-news',
      '/api/usda/nass',
      '/api/usda/commodity-list',
      '/api/commodity-list',
      '/api/categories',
      '/api/sources'
    ];

    for (const endpoint of usdaEndpoints) {
      try {
        console.log(`   Testing: ${this.SERVER_BASE_URL}${endpoint}`);
        const response = await axios.get(`${this.SERVER_BASE_URL}${endpoint}`, {
          timeout: 5000
        });

        if (response.status === 200) {
          console.log(`   ✅ ${endpoint}: Available`);
          this.results.sources_explored.push({
            endpoint,
            success: true,
            data_preview: JSON.stringify(response.data).substring(0, 200)
          });
        }
      } catch (error) {
        console.log(`   ❌ ${endpoint}: ${error.message}`);
        this.results.sources_explored.push({
          endpoint,
          success: false,
          error: error.message
        });
      }
    }
  }

  async saveResults(foundItems) {
    // Save enhanced commodity list
    const enhancedCommodities = {
      timestamp: new Date().toISOString(),
      total_found: foundItems.length,
      commodities: foundItems.map(item => ({
        name: item.commodity,
        display_name: item.commodity.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        price: item.data?.currentPrice,
        unit: item.data?.unit,
        category: this.categorizeItem(item.commodity),
        source: item.data?.source || 'unknown'
      }))
    };

    await fs.writeFile(
      path.join(this.dataDir, 'enhanced_commodity_list.json'),
      JSON.stringify(enhancedCommodities, null, 2)
    );

    // Save detailed results
    await fs.writeFile(
      path.join(this.dataDir, 'bulk_exploration_results.json'),
      JSON.stringify(this.results, null, 2)
    );

    console.log(`\n💾 Results saved to: ${this.dataDir}`);
  }

  categorizeItem(commodity) {
    const categories = {
      proteins: ['chicken', 'beef', 'pork', 'turkey', 'salmon', 'tuna', 'shrimp', 'lobster', 'eggs', 'duck', 'lamb', 'goat', 'crab', 'oyster', 'scallop'],
      grains: ['wheat', 'corn', 'rice', 'oats', 'barley', 'flour', 'quinoa', 'buckwheat', 'millet'],
      vegetables: ['tomato', 'potato', 'onion', 'carrot', 'lettuce', 'spinach', 'cabbage', 'celery', 'broccoli', 'cauliflower'],
      fruits: ['apple', 'banana', 'orange', 'lemon', 'lime', 'strawberry', 'blueberry', 'grape'],
      dairy: ['milk', 'butter', 'cheese', 'cream', 'yogurt'],
      oils: ['olive-oil', 'canola-oil', 'vegetable-oil', 'sunflower-oil'],
      nuts: ['almond', 'walnut', 'pecan', 'pistachio', 'cashew'],
      spices: ['basil', 'cilantro', 'parsley', 'garlic', 'ginger', 'pepper', 'salt', 'cinnamon'],
      beverages: ['coffee', 'tea', 'cocoa']
    };

    for (const [category, items] of Object.entries(categories)) {
      if (items.some(item => commodity.includes(item) || item.includes(commodity))) {
        return category;
      }
    }
    return 'other';
  }

  async generateChefFriendlyFeatures(foundItems) {
    console.log(`\n🍳 Generating chef-friendly features...`);

    // Seasonal pricing analysis
    const seasonalItems = foundItems.filter(item =>
      ['strawberry', 'blueberry', 'asparagus', 'tomato', 'peach', 'apple'].includes(item.commodity)
    );

    // Popular cooking combinations
    const cookingCombinations = [
      { name: 'Italian Basics', items: ['tomato', 'basil', 'mozzarella', 'olive-oil'] },
      { name: 'Asian Stir-Fry', items: ['ginger', 'garlic', 'soy-sauce', 'sesame-oil'] },
      { name: 'Breakfast Essentials', items: ['eggs', 'bacon', 'butter', 'milk'] },
      { name: 'Baking Basics', items: ['flour', 'sugar', 'butter', 'eggs', 'vanilla'] },
      { name: 'Salad Foundations', items: ['lettuce', 'tomato', 'cucumber', 'olive-oil'] }
    ];

    // Price volatility analysis
    const volatileItems = foundItems.filter(item => {
      const change = parseFloat(item.data?.priceChangePercent || '0');
      return Math.abs(change) > 5; // Items with >5% change
    });

    const features = {
      timestamp: new Date().toISOString(),
      seasonal_items: seasonalItems.length,
      cooking_combinations: cookingCombinations.length,
      high_volatility_items: volatileItems.length,
      total_commodities: foundItems.length,
      chef_recommendations: {
        seasonal_focus: seasonalItems.map(item => item.commodity),
        volatile_pricing: volatileItems.map(item => ({
          commodity: item.commodity,
          change_percent: item.data?.priceChangePercent
        })),
        cost_effective: foundItems
          .filter(item => parseFloat(item.data?.currentPrice || '999') < 3)
          .map(item => item.commodity)
          .slice(0, 10)
      }
    };

    await fs.writeFile(
      path.join(this.dataDir, 'chef_features.json'),
      JSON.stringify(features, null, 2)
    );

    return features;
  }

  async run() {
    console.log('🚀 Enhanced Foodberg Data Collection Starting...\n');

    await this.initialize();

    // Step 1: Bulk commodity exploration
    const foundItems = await this.exploreBulkCommodities();

    // Step 2: USDA endpoint exploration
    await this.exploreUSDAEndpoints();

    // Step 3: Generate chef-friendly features
    const features = await this.generateChefFriendlyFeatures(foundItems);

    // Step 4: Save all results
    await this.saveResults(foundItems);

    // Final report
    console.log('\n📊 Enhanced Collection Summary:');
    console.log(`   Total commodities tested: ${this.results.total_attempts}`);
    console.log(`   Successfully found: ${this.results.successful}`);
    console.log(`   Failed attempts: ${this.results.failed}`);
    console.log(`   Success rate: ${(this.results.successful/this.results.total_attempts*100).toFixed(1)}%`);
    console.log(`   USDA endpoints explored: ${this.results.sources_explored.length}`);
    console.log(`   Chef features generated: ${features.cooking_combinations.length} combinations`);
    console.log(`   High volatility items: ${features.chef_recommendations.volatile_pricing.length}`);

    console.log('\n✨ Enhanced data collection complete!');
    console.log(`   📁 Results stored in: ${this.dataDir}`);
    console.log(`   🔍 New commodities discovered: ${this.results.successful - 70} additional items`);

    return {
      total_found: foundItems.length,
      new_items: this.results.successful - 70,
      features_generated: features
    };
  }
}

// Run if called directly
if (require.main === module) {
  const collector = new EnhancedDataCollector();
  collector.run().catch(error => {
    console.error('\n💥 Enhanced collection failed:', error.message);
    process.exit(1);
  });
}

module.exports = { EnhancedDataCollector };