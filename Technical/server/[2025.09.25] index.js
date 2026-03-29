const express = require('express');
const cors = require('cors');
const fs = require('fs').promises;
const path = require('path');
const { getUSDAClient } = require('../lib/usdaApi.js');
// const { MultiSourceDataClient } = require('../lib/multi-source-client.js');

const app = express();
const PORT = process.env.PORT || 3001;

const HISTORICAL_DATA_DIR = path.join(__dirname, '..', 'data', 'historical');
const CONFIG_DIR = path.join(__dirname, '..', 'config');

// Initialize clients
let usdaClient = null;
let multiSourceClient = null;

async function initializeDataSources() {
  try {
    // Load configuration files
    const apiKeysPath = path.join(CONFIG_DIR, 'api-keys.json');
    const dataSourcesPath = path.join(CONFIG_DIR, 'data-sources.json');

    const apiKeysData = await fs.readFile(apiKeysPath, 'utf8');
    const dataSourcesData = await fs.readFile(dataSourcesPath, 'utf8');

    const apiKeysConfig = JSON.parse(apiKeysData);
    const dataSourcesConfig = JSON.parse(dataSourcesData);

    // Initialize original USDA client for backwards compatibility
    const fdcApiKey = apiKeysConfig.primary_sources?.usda_fdc_api_key;
    const marsApiKey = apiKeysConfig.primary_sources?.usda_mars_api_key !== 'YOUR_MARS_API_KEY_HERE'
      ? apiKeysConfig.primary_sources.usda_mars_api_key
      : null;

    usdaClient = getUSDAClient(fdcApiKey, marsApiKey);

    // Initialize multi-source client
    // multiSourceClient = new MultiSourceDataClient(dataSourcesConfig, apiKeysConfig);

    // Report initialization status
    console.log('🚀 Data Sources Initialization Complete');
    console.log('📊 Available Sources:');

    if (marsApiKey) {
      console.log('  ✅ USDA Market News API - Live data available');
    } else {
      console.log('  ⚠️  USDA Market News API key not configured');
    }

    // Check other API keys
    const availableSources = [];
    const unavailableSources = [];

    Object.entries(dataSourcesConfig.sources).forEach(([sourceName, sourceConfig]) => {
      if (sourceConfig.api_key_required && sourceConfig.api_key_field) {
        const keyField = sourceConfig.api_key_field;
        const hasKey = multiSourceClient.getApiKey(keyField) !== null;

        if (hasKey) {
          availableSources.push(sourceName);
          console.log(`  ✅ ${sourceConfig.name} - Available`);
        } else {
          unavailableSources.push(sourceName);
          console.log(`  ⚠️  ${sourceConfig.name} - API key not configured`);
        }
      } else if (!sourceConfig.api_key_required) {
        availableSources.push(sourceName);
        console.log(`  ✅ ${sourceConfig.name} - Available (no key required)`);
      }
    });

    console.log(`\n📈 Data Collection Strategy:`);
    console.log(`  • Available sources: ${availableSources.length}`);
    console.log(`  • Fallback sources: ${unavailableSources.length}`);
    console.log(`  • Historical data: Always available`);

  } catch (error) {
    console.error('Failed to initialize data sources:', error.message);
    console.log('⚠️  Using historical data only');
  }
}

// Initialize on startup
initializeDataSources();

app.use(cors());
app.use(express.json());

// Endpoint to get a list of all available commodities
app.get('/api/commodities', async (req, res) => {
  try {
    const files = await fs.readdir(HISTORICAL_DATA_DIR);
    const commodities = files
      .filter(file => file.endsWith('.json'))
      .map(file => file.replace('.json', ''));
    res.json(commodities);
  } catch (error) {
    console.error('Error fetching commodity list:', error);
    res.status(500).json({ error: 'Failed to fetch commodity list' });
  }
});

// Endpoint to get the latest price for a commodity
app.get('/api/prices/:commodity', async (req, res) => {
  const { commodity } = req.params;
  const filePath = path.join(HISTORICAL_DATA_DIR, `${commodity}.json`);

  try {
    const data = await fs.readFile(filePath, 'utf8');
    const commodityData = JSON.parse(data);

    if (!commodityData.historicalData || commodityData.historicalData.length === 0) {
      return res.status(404).json({ error: 'No price data available' });
    }

    const historicalData = commodityData.historicalData;
    const latestPrice = historicalData[historicalData.length - 1];
    const previousPrice = historicalData.length > 1 ? historicalData[historicalData.length - 2] : null;

    const priceChange = previousPrice ? latestPrice.price - previousPrice.price : 0;
    const priceChangePercent = previousPrice ? (priceChange / previousPrice.price) * 100 : 0;

    res.json({
      commodity: commodityData.commodity || commodity,
      currentPrice: latestPrice.price,
      priceChange: priceChange.toFixed(2),
      priceChangePercent: priceChangePercent.toFixed(2),
      lastUpdated: latestPrice.date,
      unit: commodityData.unit || 'USD',
      category: commodityData.category,
      source: commodityData.source
    });
  } catch (error) {
    console.error(`Error fetching price for ${commodity}:`, error);
    res.status(404).json({ error: 'Commodity not found' });
  }
});

// Endpoint to get historical data for a commodity
app.get('/api/historical/:commodity', async (req, res) => {
  const { commodity } = req.params;
  const filePath = path.join(HISTORICAL_DATA_DIR, `${commodity}.json`);

  try {
    const data = await fs.readFile(filePath, 'utf8');
    const commodityData = JSON.parse(data);

    if (!commodityData.historicalData) {
      return res.status(404).json({ error: 'No historical data available' });
    }

    res.json({
      commodity: commodityData.commodity || commodity,
      category: commodityData.category,
      unit: commodityData.unit,
      source: commodityData.source,
      historicalData: commodityData.historicalData
    });
  } catch (error) {
    console.error(`Error fetching historical data for ${commodity}:`, error);
    res.status(404).json({ error: 'Commodity not found' });
  }
});

// New Live USDA API Endpoints

// Get live commodity search from USDA Market News
app.get('/api/live/search/:query', async (req, res) => {
  const { query } = req.params;
  try {
    if (usdaClient) {
      const results = await usdaClient.searchCommodities(query);
      res.json({
        query,
        results,
        source: 'USDA Market News API',
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(503).json({ error: 'USDA API not available - check configuration' });
    }
  } catch (error) {
    console.error('Live search error:', error);
    res.status(500).json({ error: 'Failed to search commodities' });
  }
});

// Get live commodity price from USDA Market News
app.get('/api/live/price/:commodity', async (req, res) => {
  const { commodity } = req.params;
  try {
    if (usdaClient) {
      const priceData = await usdaClient.getCommodityPrice(commodity);
      if (priceData) {
        res.json({
          commodity,
          data: priceData,
          source: 'USDA Market News API',
          timestamp: new Date().toISOString()
        });
      } else {
        res.status(404).json({ error: 'No live price data found for this commodity' });
      }
    } else {
      res.status(503).json({ error: 'USDA Market News API not available - check configuration' });
    }
  } catch (error) {
    console.error('Live price error:', error);
    res.status(500).json({ error: 'Failed to get live price data' });
  }
});

// Get USDA Market Types
app.get('/api/live/market-types', async (req, res) => {
  try {
    if (usdaClient) {
      const marketTypes = await usdaClient.getMarketTypes();
      res.json({
        marketTypes,
        source: 'USDA Market News API',
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(503).json({ error: 'USDA API not available' });
    }
  } catch (error) {
    console.error('Market types error:', error);
    res.status(500).json({ error: 'Failed to get market types' });
  }
});

// Get USDA Offices (Market Locations)
app.get('/api/live/offices', async (req, res) => {
  try {
    if (usdaClient) {
      const offices = await usdaClient.getOffices();
      res.json({
        offices,
        source: 'USDA Market News API',
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(503).json({ error: 'USDA API not available' });
    }
  } catch (error) {
    console.error('Offices error:', error);
    res.status(500).json({ error: 'Failed to get offices' });
  }
});

// Get USDA Reports for commodity
app.get('/api/live/reports/:commodity', async (req, res) => {
  const { commodity } = req.params;
  const { startDate, endDate, reportType } = req.query;

  try {
    if (usdaClient) {
      const reports = await usdaClient.getReports(commodity, startDate, endDate, reportType);
      res.json({
        commodity,
        reports,
        query: { startDate, endDate, reportType },
        source: 'USDA Market News API',
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(503).json({ error: 'USDA API not available' });
    }
  } catch (error) {
    console.error('Reports error:', error);
    res.status(500).json({ error: 'Failed to get reports' });
  }
});

// Multi-Source Data Collection Endpoints

// Get commodity price from all available sources
app.get('/api/multi/:commodity', async (req, res) => {
  const { commodity } = req.params;
  try {
    if (multiSourceClient) {
      const results = await multiSourceClient.getCommodityPrice(commodity);
      res.json(results);
    } else {
      res.status(503).json({ error: 'Multi-source client not available' });
    }
  } catch (error) {
    console.error('Multi-source price error:', error);
    res.status(500).json({ error: 'Failed to get multi-source price data' });
  }
});

// Get historical data from multiple sources
app.get('/api/multi/:commodity/historical', async (req, res) => {
  const { commodity } = req.params;
  const { days = 30 } = req.query;

  try {
    if (multiSourceClient) {
      const results = await multiSourceClient.getHistoricalPrices(commodity, parseInt(days));
      res.json(results);
    } else {
      res.status(503).json({ error: 'Multi-source client not available' });
    }
  } catch (error) {
    console.error('Multi-source historical error:', error);
    res.status(500).json({ error: 'Failed to get multi-source historical data' });
  }
});

// Bulk data collection endpoint - collect and store data for multiple commodities
app.post('/api/collect/bulk', async (req, res) => {
  const { commodities, sources } = req.body;

  if (!commodities || !Array.isArray(commodities)) {
    return res.status(400).json({ error: 'commodities array required' });
  }

  const results = {
    total_commodities: commodities.length,
    successful: 0,
    failed: 0,
    results: [],
    collection_timestamp: new Date().toISOString()
  };

  try {
    for (const commodity of commodities) {
      try {
        console.log(`Collecting data for: ${commodity}`);
        const commodityData = await multiSourceClient.getCommodityPrice(commodity, { sources });

        results.results.push({
          commodity,
          success: true,
          sources_used: commodityData.sources.length,
          confidence: commodityData.confidence_level,
          primary_price: commodityData.primary_price
        });

        results.successful++;
      } catch (error) {
        console.error(`Failed to collect data for ${commodity}:`, error.message);
        results.results.push({
          commodity,
          success: false,
          error: error.message
        });
        results.failed++;
      }
    }

    res.json(results);
  } catch (error) {
    console.error('Bulk collection error:', error);
    res.status(500).json({ error: 'Failed to perform bulk collection' });
  }
});

// Data sources status endpoint
app.get('/api/sources/status', (req, res) => {
  if (!multiSourceClient) {
    return res.status(503).json({ error: 'Multi-source client not available' });
  }

  const status = {
    timestamp: new Date().toISOString(),
    sources: {},
    summary: {
      total_sources: 0,
      available_sources: 0,
      configured_apis: 0,
      free_sources: 0
    }
  };

  Object.entries(multiSourceClient.config.sources).forEach(([sourceName, sourceConfig]) => {
    const hasApiKey = sourceConfig.api_key_required
      ? multiSourceClient.getApiKey(sourceConfig.api_key_field) !== null
      : true;

    status.sources[sourceName] = {
      name: sourceConfig.name,
      type: sourceConfig.type,
      available: hasApiKey,
      cost: sourceConfig.cost,
      update_frequency: sourceConfig.update_frequency,
      reliability: sourceConfig.reliability,
      api_key_required: sourceConfig.api_key_required
    };

    status.summary.total_sources++;
    if (hasApiKey) status.summary.available_sources++;
    if (sourceConfig.api_key_required && hasApiKey) status.summary.configured_apis++;
    if (sourceConfig.cost === 'free') status.summary.free_sources++;
  });

  res.json(status);
});

// Enhanced health check endpoint
app.get('/api/health', (req, res) => {
  const health = {
    status: 'OK',
    timestamp: new Date().toISOString(),
    services: {
      historical_data: 'Available',
      usda_api: usdaClient ? 'Available' : 'Not configured',
      multi_source_client: multiSourceClient ? 'Available' : 'Not available'
    },
    data_sources: {
      historical_files: 'Available',
      live_apis: 0,
      scraping_sources: 0,
      total_sources: 0
    }
  };

  if (multiSourceClient) {
    Object.entries(multiSourceClient.config.sources).forEach(([sourceName, sourceConfig]) => {
      health.data_sources.total_sources++;

      if (sourceConfig.type === 'api') {
        const hasApiKey = sourceConfig.api_key_required
          ? multiSourceClient.getApiKey(sourceConfig.api_key_field) !== null
          : true;
        if (hasApiKey) health.data_sources.live_apis++;
      } else if (sourceConfig.type === 'scraping') {
        health.data_sources.scraping_sources++;
      }
    });
  }

  res.json(health);
});

app.listen(PORT, () => {
  console.log(`🚀 Foodberg Server running on port ${PORT}`);
  console.log(`📊 Historical data: ${HISTORICAL_DATA_DIR}`);
  console.log(`🔑 API Status: ${usdaClient ? 'Live + Historical' : 'Historical only'}`);
});