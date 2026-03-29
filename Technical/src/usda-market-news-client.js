/**
 * USDA MyMarketNews API Client
 * Provides access to terminal market prices and agricultural commodity data
 * API Documentation: https://mymarketnews.ams.usda.gov/mymarketnews-api
 */

const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');

class USDAMarketNewsClient {
  constructor() {
    this.baseURL = 'https://mymarketnews.ams.usda.gov/api/v1';
    this.cacheDir = path.join(__dirname, '..', '..', 'data', 'cache', 'usda');
    this.cacheDuration = 3600000; // 1 hour cache

    // Terminal market report IDs for major cities
    this.terminalMarkets = {
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
    };

    // Common commodity mappings
    this.commodityMappings = {
      // Vegetables
      'tomatoes': ['TOMATOES', 'TOMATO'],
      'potatoes': ['POTATOES', 'POTATO'],
      'onions': ['ONIONS', 'ONION', 'DRY ONIONS'],
      'lettuce': ['LETTUCE', 'ICEBERG', 'ROMAINE'],
      'carrots': ['CARROTS', 'CARROT'],
      'celery': ['CELERY'],
      'broccoli': ['BROCCOLI'],
      'cauliflower': ['CAULIFLOWER'],
      'cabbage': ['CABBAGE', 'GREEN CABBAGE', 'RED CABBAGE'],
      'peppers': ['PEPPERS', 'BELL PEPPERS', 'GREEN PEPPERS'],

      // Fruits
      'apples': ['APPLES', 'APPLE'],
      'oranges': ['ORANGES', 'ORANGE', 'NAVEL'],
      'bananas': ['BANANAS', 'BANANA'],
      'strawberries': ['STRAWBERRIES', 'STRAWBERRY'],
      'grapes': ['GRAPES', 'GRAPE'],
      'lemons': ['LEMONS', 'LEMON'],
      'limes': ['LIMES', 'LIME'],
      'avocados': ['AVOCADOS', 'AVOCADO', 'HASS'],

      // Proteins (from other reports)
      'eggs': ['EGGS', 'SHELL EGGS'],
      'chicken': ['CHICKEN', 'BROILER', 'FRYER'],
      'beef': ['BEEF', 'CATTLE'],
      'pork': ['PORK', 'HOGS']
    };
  }

  /**
   * Initialize cache directory
   */
  async initCache() {
    try {
      await fs.mkdir(this.cacheDir, { recursive: true });
    } catch (error) {
      console.error('Error creating cache directory:', error);
    }
  }

  /**
   * Get cached data if available and fresh
   */
  async getCachedData(cacheKey) {
    try {
      const cacheFile = path.join(this.cacheDir, `${cacheKey}.json`);
      const stats = await fs.stat(cacheFile);

      if (Date.now() - stats.mtimeMs < this.cacheDuration) {
        const data = await fs.readFile(cacheFile, 'utf8');
        return JSON.parse(data);
      }
    } catch (error) {
      // Cache miss or error, will fetch fresh data
    }
    return null;
  }

  /**
   * Save data to cache
   */
  async saveToCache(cacheKey, data) {
    try {
      const cacheFile = path.join(this.cacheDir, `${cacheKey}.json`);
      await fs.writeFile(cacheFile, JSON.stringify(data, null, 2));
    } catch (error) {
      console.error('Error saving to cache:', error);
    }
  }

  /**
   * Fetch terminal market prices for a specific market
   */
  async getTerminalMarketPrices(market = 'new_york', date = null) {
    await this.initCache();

    const reportId = this.terminalMarkets[market.toLowerCase()] || this.terminalMarkets['new_york'];
    const dateStr = date || new Date().toISOString().split('T')[0];
    const cacheKey = `terminal_${market}_${dateStr}`;

    // Check cache first
    const cached = await this.getCachedData(cacheKey);
    if (cached) {
      console.log(`Using cached data for ${market} terminal market`);
      return cached;
    }

    try {
      const url = `${this.baseURL}/reports/${reportId}`;
      const response = await axios.get(url, {
        params: {
          date: dateStr,
          format: 'json'
        },
        timeout: 10000
      });

      const processedData = this.processTerminalMarketData(response.data);
      await this.saveToCache(cacheKey, processedData);

      return processedData;
    } catch (error) {
      console.error(`Error fetching terminal market data for ${market}:`, error.message);
      return null;
    }
  }

  /**
   * Process raw terminal market data into structured format
   */
  processTerminalMarketData(rawData) {
    const processed = {
      timestamp: new Date().toISOString(),
      market: rawData.market || 'Unknown',
      reportDate: rawData.report_date,
      commodities: {}
    };

    // Parse the data based on USDA format
    if (rawData.results && Array.isArray(rawData.results)) {
      rawData.results.forEach(item => {
        const commodity = item.commodity_name?.toLowerCase() || 'unknown';
        const variety = item.variety || 'standard';
        const unit = item.unit || 'each';
        const lowPrice = parseFloat(item.low_price) || 0;
        const highPrice = parseFloat(item.high_price) || 0;
        const avgPrice = (lowPrice + highPrice) / 2;

        if (!processed.commodities[commodity]) {
          processed.commodities[commodity] = [];
        }

        processed.commodities[commodity].push({
          variety,
          unit,
          lowPrice,
          highPrice,
          avgPrice,
          origin: item.origin || 'Unknown',
          grade: item.grade || 'Standard',
          condition: item.condition || 'Good'
        });
      });
    }

    return processed;
  }

  /**
   * Get prices for specific commodities across all terminal markets
   */
  async getCommodityPricesAcrossMarkets(commodity) {
    const results = {
      commodity,
      timestamp: new Date().toISOString(),
      markets: {}
    };

    // Fetch from all major markets in parallel
    const marketPromises = Object.keys(this.terminalMarkets).map(async market => {
      const data = await this.getTerminalMarketPrices(market);
      if (data && data.commodities) {
        // Search for commodity in various forms
        const searchTerms = this.commodityMappings[commodity.toLowerCase()] || [commodity.toUpperCase()];

        for (const term of searchTerms) {
          const commodityData = data.commodities[term.toLowerCase()];
          if (commodityData) {
            results.markets[market] = commodityData;
            break;
          }
        }
      }
    });

    await Promise.all(marketPromises);

    // Calculate national average if data available
    if (Object.keys(results.markets).length > 0) {
      let totalPrice = 0;
      let count = 0;

      Object.values(results.markets).forEach(marketData => {
        marketData.forEach(item => {
          totalPrice += item.avgPrice;
          count++;
        });
      });

      results.nationalAverage = count > 0 ? (totalPrice / count).toFixed(2) : 0;
    }

    return results;
  }

  /**
   * Get all available commodities from a market
   */
  async getAvailableCommodities(market = 'new_york') {
    const data = await this.getTerminalMarketPrices(market);

    if (data && data.commodities) {
      return Object.keys(data.commodities).sort();
    }

    return [];
  }

  /**
   * Search for reports by commodity
   */
  async searchReportsByCommodity(commodity) {
    try {
      const url = `${this.baseURL}/reports/search`;
      const response = await axios.get(url, {
        params: {
          commodity: commodity.toUpperCase(),
          format: 'json'
        },
        timeout: 10000
      });

      return response.data;
    } catch (error) {
      console.error(`Error searching reports for ${commodity}:`, error.message);
      return null;
    }
  }

  /**
   * Get historical price data for trend analysis
   */
  async getHistoricalPrices(commodity, market = 'new_york', days = 30) {
    const historicalData = {
      commodity,
      market,
      period: `${days} days`,
      data: []
    };

    // Generate date range
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    // Fetch data for each date (limited to avoid overwhelming the API)
    // In production, this should be done with batch requests or stored historical data
    const dates = [];
    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 7)) {
      dates.push(new Date(d).toISOString().split('T')[0]);
    }

    for (const date of dates) {
      const data = await this.getTerminalMarketPrices(market, date);
      if (data && data.commodities) {
        const searchTerms = this.commodityMappings[commodity.toLowerCase()] || [commodity.toUpperCase()];

        for (const term of searchTerms) {
          const commodityData = data.commodities[term.toLowerCase()];
          if (commodityData && commodityData.length > 0) {
            historicalData.data.push({
              date,
              price: commodityData[0].avgPrice,
              low: commodityData[0].lowPrice,
              high: commodityData[0].highPrice
            });
            break;
          }
        }
      }

      // Rate limiting delay
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    return historicalData;
  }

  /**
   * Export data to Excel format
   */
  async exportToExcel(data, filename) {
    const outputPath = path.join(__dirname, '..', '..', '..', 'Output', 'Data', filename);

    // Convert to CSV format for Excel compatibility
    let csv = 'Commodity,Market,Variety,Unit,Low Price,High Price,Average Price,Origin,Grade\n';

    if (data.markets) {
      Object.entries(data.markets).forEach(([market, items]) => {
        items.forEach(item => {
          csv += `"${data.commodity}","${market}","${item.variety}","${item.unit}",`;
          csv += `${item.lowPrice},${item.highPrice},${item.avgPrice},`;
          csv += `"${item.origin}","${item.grade}"\n`;
        });
      });
    }

    await fs.writeFile(outputPath.replace('.xlsx', '.csv'), csv);
    console.log(`Data exported to ${outputPath}`);

    return outputPath;
  }
}

// Export for use in other modules
module.exports = USDAMarketNewsClient;

// Example usage
if (require.main === module) {
  (async () => {
    const client = new USDAMarketNewsClient();

    console.log('Fetching New York terminal market prices...');
    const nyPrices = await client.getTerminalMarketPrices('new_york');
    console.log('Available commodities:', Object.keys(nyPrices.commodities || {}).slice(0, 10));

    console.log('\nFetching tomato prices across all markets...');
    const tomatoPrices = await client.getCommodityPricesAcrossMarkets('tomatoes');
    console.log('Tomato prices:', JSON.stringify(tomatoPrices, null, 2));

    console.log('\nFetching historical prices for potatoes...');
    const historicalPrices = await client.getHistoricalPrices('potatoes', 'chicago', 14);
    console.log('Historical data points:', historicalPrices.data.length);

    // Export sample data
    if (tomatoPrices.markets && Object.keys(tomatoPrices.markets).length > 0) {
      await client.exportToExcel(tomatoPrices, 'tomato_market_prices.csv');
    }
  })();
}