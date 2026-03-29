#!/usr/bin/env node

/**
 * Foodberg Data Collection Script
 * Collects food commodity data from multiple sources and stores for offline use
 */

const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');

const SERVER_BASE_URL = 'http://localhost:3001';

class DataCollector {
  constructor() {
    this.commodities = [
      // Grains & Cereals
      'wheat', 'corn', 'rice', 'oats', 'barley', 'flour',

      // Proteins
      'chicken', 'chicken-breast', 'beef', 'beef-brisket', 'pork', 'pork-loin',
      'turkey', 'eggs', 'salmon', 'tuna', 'shrimp', 'lobster',
      'cattle', 'hogs', 'soybeans',

      // Dairy
      'milk', 'butter', 'cheese', 'cheese-cheddar', 'whey',

      // Oils & Fats
      'olive-oil', 'canola-oil', 'vegetable-oil', 'sunflower-oil',

      // Vegetables
      'tomatoes', 'tomato', 'potatoes', 'potato', 'onions', 'onion',
      'carrots', 'carrot', 'lettuce', 'spinach', 'cabbage', 'celery',

      // Fruits
      'apple', 'banana', 'orange', 'lemon', 'lime', 'strawberry',
      'blueberry', 'grape',

      // Nuts & Seeds
      'almond', 'walnut', 'pecan', 'pistachio',

      // Herbs & Spices
      'basil', 'cilantro', 'parsley', 'garlic', 'ginger', 'pepper',
      'salt', 'cinnamon', 'cloves', 'nutmeg', 'saffron', 'vanilla',

      // Beverages & Other
      'coffee', 'tea', 'cocoa', 'sugar', 'sugar-white', 'yeast',
      'juice', 'truffle'
    ];
    this.dataDir = path.join(__dirname, '..', 'data', 'collected');
    this.results = {
      timestamp: new Date().toISOString(),
      total_commodities: this.commodities.length,
      successful: 0,
      failed: 0,
      sources_used: new Set(),
      results: []
    };
  }

  async initialize() {
    try {
      await fs.mkdir(this.dataDir, { recursive: true });
      console.log(`📁 Data directory: ${this.dataDir}`);
    } catch (error) {
      console.error('Failed to create data directory:', error.message);
    }
  }

  async checkServerStatus() {
    try {
      const response = await axios.get(`${SERVER_BASE_URL}/api/health`, { timeout: 5000 });
      console.log('🟢 Server Status:', response.data.status);
      console.log('📊 Available Sources:', response.data.data_sources?.total_sources || 'Unknown');
      return true;
    } catch (error) {
      console.error('🔴 Server not available:', error.message);
      console.log('   Make sure to run: npm run server');
      return false;
    }
  }

  async collectSingleCommodity(commodity) {
    try {
      console.log(`   Collecting: ${commodity}...`);

      // Try multi-source endpoint first
      let response = null;
      let dataSource = 'unknown';
      let price = null;
      let sources = [];

      try {
        response = await axios.get(`${SERVER_BASE_URL}/api/multi/${commodity}`, { timeout: 30000 });
        if (response.data && response.data.primary_price) {
          price = response.data.primary_price;
          sources = response.data.sources.map(s => s.name);
          dataSource = 'multi-source';
          sources.forEach(s => this.results.sources_used.add(s));
        }
      } catch (multiError) {
        // Fall back to historical data
        try {
          response = await axios.get(`${SERVER_BASE_URL}/api/prices/${commodity}`, { timeout: 15000 });
          if (response.data && response.data.currentPrice) {
            price = response.data.currentPrice;
            sources = ['historical_data'];
            dataSource = 'historical';
            this.results.sources_used.add('historical_data');
          }
        } catch (historicalError) {
          throw new Error(`Both multi-source and historical failed: ${multiError.message}, ${historicalError.message}`);
        }
      }

      const result = {
        commodity,
        success: true,
        price: price,
        data_source: dataSource,
        sources: sources,
        collected_at: new Date().toISOString(),
        raw_data: response.data
      };

      // Store individual commodity data
      await this.storeCommodityData(commodity, result);

      this.results.results.push({
        commodity,
        success: true,
        price: price,
        sources: sources.length,
        data_source: dataSource
      });

      this.results.successful++;
      console.log(`   ✅ ${commodity}: $${price} (${sources.join(', ')})`);

    } catch (error) {
      console.log(`   ❌ ${commodity}: ${error.message}`);
      this.results.results.push({
        commodity,
        success: false,
        error: error.message
      });
      this.results.failed++;
    }
  }

  async storeCommodityData(commodity, data) {
    try {
      const filename = `${commodity}_${new Date().toISOString().split('T')[0]}.json`;
      const filepath = path.join(this.dataDir, filename);
      await fs.writeFile(filepath, JSON.stringify(data, null, 2));
    } catch (error) {
      console.error(`Failed to store data for ${commodity}:`, error.message);
    }
  }

  async collectAll() {
    console.log('\n🚀 Starting bulk food commodity data collection...');
    console.log(`📋 Commodities to collect: ${this.commodities.length}`);

    const batchSize = 5; // Process in batches to avoid overwhelming sources
    for (let i = 0; i < this.commodities.length; i += batchSize) {
      const batch = this.commodities.slice(i, i + batchSize);
      console.log(`\n📦 Processing batch ${Math.floor(i/batchSize) + 1}/${Math.ceil(this.commodities.length/batchSize)}:`);

      const promises = batch.map(commodity => this.collectSingleCommodity(commodity));
      await Promise.allSettled(promises);

      // Small delay between batches
      if (i + batchSize < this.commodities.length) {
        console.log('   ⏱️  Waiting 2 seconds...');
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
  }

  async generateSummary() {
    console.log('\n📊 Collection Summary:');
    console.log(`   Total commodities: ${this.results.total_commodities}`);
    console.log(`   Successful: ${this.results.successful}`);
    console.log(`   Failed: ${this.results.failed}`);
    console.log(`   Success rate: ${((this.results.successful / this.results.total_commodities) * 100).toFixed(1)}%`);
    console.log(`   Sources used: ${Array.from(this.results.sources_used).join(', ')}`);

    // Store summary
    const summaryPath = path.join(this.dataDir, `collection_summary_${new Date().toISOString().split('T')[0]}.json`);
    await fs.writeFile(summaryPath, JSON.stringify({
      ...this.results,
      sources_used: Array.from(this.results.sources_used)
    }, null, 2));

    console.log(`\n💾 Data stored in: ${this.dataDir}`);
    console.log(`📄 Summary saved: ${path.basename(summaryPath)}`);

    return this.results;
  }

  async run() {
    await this.initialize();

    const serverRunning = await this.checkServerStatus();
    if (!serverRunning) {
      process.exit(1);
    }

    await this.collectAll();
    await this.generateSummary();

    console.log('\n✨ Data collection complete!');
    console.log('   Use this data for offline access when APIs are unavailable');
  }
}

// Run if called directly
if (require.main === module) {
  const collector = new DataCollector();
  collector.run().catch(error => {
    console.error('\n💥 Collection failed:', error.message);
    process.exit(1);
  });
}

module.exports = { DataCollector };