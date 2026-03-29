# Foodberg Technical Implementation Guide

## Architecture Overview

Foodberg is a professional food cost management system built with Next.js and Node.js, designed for restaurant operations and professional chefs. The system integrates multiple data sources to provide real-time pricing, recipe costing, and comprehensive analytics.

### System Components

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                 │
│  - React Components                                  │
│  - Tailwind CSS                                      │
│  - Recharts Visualization                            │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│                  API Layer (Next.js API)             │
│  - REST Endpoints                                    │
│  - Data Validation                                   │
│  - Authentication                                    │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│              Backend Services (Node.js)              │
│  ┌──────────────────────────────────────────────┐   │
│  │  USDA Market News Client                     │   │
│  │  - Terminal Market Prices                    │   │
│  │  - Historical Data                           │   │
│  └──────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────┐   │
│  │  Recipe Costing Engine                       │   │
│  │  - Yield Calculations                        │   │
│  │  - Menu Engineering                          │   │
│  └──────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────┐   │
│  │  Data Collection Scheduler                   │   │
│  │  - Automated Updates                         │   │
│  │  - Cache Management                          │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│              External Data Sources                   │
│  - USDA MyMarketNews API                            │
│  - FAO Food Price Index                             │
│  - World Bank Commodities                           │
│  - API Ninja                                        │
│  - Vendor APIs (Sysco, US Foods, Baldor)            │
└──────────────────────────────────────────────────────┘
```

## Directory Structure

```
Technical/
├── src/                          # Source code
│   ├── usda-market-news-client.js    # USDA API integration
│   ├── recipe-costing-engine.js      # Recipe cost calculations
│   └── vendor-price-tracker.js       # Vendor comparison (planned)
├── scripts/                      # Data collection scripts
│   ├── collect-data.js               # Basic data collection
│   ├── download-free-data.js         # Free source downloads
│   ├── enhanced-bulk-collection.js   # Bulk collection
│   └── data-scheduler.js             # Automated scheduling (planned)
├── server/                       # Backend server
│   ├── index.js                      # Express server
│   └── routes/                       # API routes
├── data_processors/              # Data transformation
│   └── normalize-data.js             # Data normalization
├── docs/                         # Technical documentation
│   ├── api-documentation.md          # API specs
│   ├── methodology-report.tex        # LaTeX report source
│   └── data-sources.md               # Data source guide
└── configs/                      # Configuration files
    ├── commodities.json              # Commodity definitions
    ├── vendors.json                  # Vendor configurations
    └── yields.json                   # Yield percentages
```

## Setup Instructions

### Prerequisites
- Node.js 18+
- npm or yarn
- API keys for data sources

### Installation

1. **Install dependencies**
```bash
cd Projects/Foodberg
npm install
```

2. **Configure environment variables**
Create `.env.local` file:
```env
# API Keys
USDA_API_KEY=your_key_here
API_NINJA_KEY=your_key_here
FAO_API_ENDPOINT=https://api.fao.org/

# Database (if using)
DATABASE_URL=your_database_url

# Authentication
JWT_SECRET=your_secret_here
```

3. **Initialize data directories**
```bash
mkdir -p data/cache/usda
mkdir -p Output/Data
mkdir -p Output/PDFs
```

4. **Run development server**
```bash
npm run dev
```

## Core Components

### USDA Market News Client (`src/usda-market-news-client.js`)

Handles all USDA Market News API interactions:

**Key Features:**
- Terminal market price fetching from 12 major US markets
- Historical data retrieval for trend analysis
- Cross-market price comparison
- Intelligent caching with TTL
- Commodity name mapping and normalization

**Usage Example:**
```javascript
const client = new USDAMarketNewsClient();

// Get current prices from New York terminal
const prices = await client.getTerminalMarketPrices('new_york');

// Compare tomato prices across all markets
const tomatoPrices = await client.getCommodityPricesAcrossMarkets('tomatoes');

// Get 30-day historical data
const historical = await client.getHistoricalPrices('potatoes', 'chicago', 30);
```

### Recipe Costing Engine (`src/recipe-costing-engine.js`)

Professional recipe costing with industry-standard calculations:

**Key Features:**
- Ingredient cost calculation with yield factors
- Cooking loss adjustments (grilling, roasting, etc.)
- Labor and overhead calculations
- Menu engineering matrix (Stars, Puzzles, Plow Horses, Dogs)
- Profit margin analysis and pricing recommendations

**Usage Example:**
```javascript
const engine = new RecipeCostingEngine();

const recipe = {
  name: 'Grilled Chicken',
  yield: 10,
  ingredients: [...],
  laborMinutes: 30,
  targetFoodCostPercent: 0.28
};

const cost = engine.calculateRecipeCost(recipe);
// Returns complete cost breakdown with suggested pricing
```

### Data Collection Scripts

#### `enhanced-bulk-collection.js`
- Collects data for 200+ commodities
- Explores multiple data sources
- Generates comprehensive reports

#### `collect-data.js`
- Basic data collection utility
- Single commodity queries
- Quick price checks

#### `download-free-data.js`
- Downloads from free sources (FAO, World Bank)
- Bulk historical data retrieval
- No API key required

## API Endpoints

### Commodity Prices
```
GET /api/prices/current
GET /api/prices/historical?commodity={name}&days={30}
GET /api/prices/terminal?market={city}
GET /api/prices/compare?commodity={name}
```

### Recipe Costing
```
POST /api/recipes/cost
GET /api/recipes/{id}
PUT /api/recipes/{id}
DELETE /api/recipes/{id}
GET /api/recipes/menu-engineering
```

### Vendor Management
```
GET /api/vendors
POST /api/vendors
GET /api/vendors/compare?commodity={name}
POST /api/vendors/{id}/prices
```

### Reports
```
GET /api/reports/weekly
GET /api/reports/menu-analysis
GET /api/reports/vendor-performance
POST /api/reports/generate
```

## Data Processing Pipeline

1. **Collection Phase**
   - Scheduled scripts fetch from external APIs
   - Rate limiting and retry logic applied
   - Raw data stored with timestamps

2. **Normalization Phase**
   - Units converted to standard measures
   - Commodity names mapped to internal IDs
   - Outliers detected and flagged

3. **Calculation Phase**
   - Yields and shrinkage applied
   - Cost rollups calculated
   - Trends and forecasts generated

4. **Delivery Phase**
   - Data formatted for frontend display
   - Excel/CSV exports generated
   - PDF reports compiled from LaTeX

## Maintenance Procedures

### Daily Tasks
```bash
# Verify data collection
node Technical/scripts/collect-data.js --verify

# Check API status
curl http://localhost:3001/api/health

# Review logs
tail -f logs/data-collection.log
```

### Weekly Tasks
```bash
# Clear cache older than 7 days
find data/cache -mtime +7 -delete

# Generate performance report
node Technical/scripts/generate-report.js --weekly

# Backup configuration
cp -r Technical/configs backups/configs-$(date +%Y%m%d)
```

### Monthly Tasks
- Review and update yield percentages
- Audit vendor configurations
- Analyze API usage and costs
- Update commodity mappings

## Troubleshooting

### Common Issues

#### API Rate Limiting
```javascript
// Implement exponential backoff
const backoff = (attempt) => Math.pow(2, attempt) * 1000;
await new Promise(resolve => setTimeout(resolve, backoff(attemptNumber)));
```

#### Data Inconsistency
- Check `data/cache/` for stale data
- Verify API credentials are current
- Review commodity mapping in `configs/commodities.json`

#### Performance Issues
- Enable caching: `ENABLE_CACHE=true`
- Reduce API call frequency
- Implement database indexing

## Extension Guide

### Adding New Data Sources

1. Create client module in `/src`:
```javascript
// src/new-source-client.js
class NewSourceClient {
  async fetchPrices() { /* implementation */ }
}
```

2. Register in data scheduler:
```javascript
// scripts/data-scheduler.js
scheduler.addSource(new NewSourceClient());
```

3. Update commodity mappings:
```json
// configs/commodities.json
{
  "tomatoes": {
    "newSource": "TOMATO_FRESH"
  }
}
```

### Adding New Features

1. Design API endpoint
2. Implement backend logic in `/src`
3. Create API route in `/server/routes`
4. Add frontend component
5. Update documentation

## Testing

### Unit Tests
```bash
npm test                 # Run all tests
npm test -- --watch      # Watch mode
npm test -- --coverage   # Coverage report
```

### Integration Tests
```bash
npm run test:integration
```

### API Testing
```bash
# Test USDA integration
node Technical/src/usda-market-news-client.js

# Test recipe costing
node Technical/src/recipe-costing-engine.js
```

## Performance Metrics

### Target Benchmarks
- API Response: <2 seconds
- Data Processing: <5 seconds for 1000 items
- Cache Hit Rate: >80%
- Data Accuracy: 99%+

### Monitoring
```javascript
// Performance tracking
console.time('api-call');
const result = await apiCall();
console.timeEnd('api-call');

// Memory usage
console.log(process.memoryUsage());
```

## Security Considerations

- **API Keys**: Store in environment variables, never commit
- **Authentication**: JWT tokens with expiration
- **Rate Limiting**: Implement per-user limits
- **Input Validation**: Sanitize all user inputs
- **HTTPS**: Required for production

## Deployment

### Production Build
```bash
npm run build
npm start
```

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY . .
RUN npm ci --only=production
CMD ["npm", "start"]
```

### Environment Configuration
```env
NODE_ENV=production
API_URL=https://api.foodberg.com
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

## Support Resources

### Internal Documentation
- `/Technical/docs/` - Technical specifications
- `/Output/README.md` - User guide
- `/HANDOFF_DOCUMENTATION.md` - Project status

### External Resources
- [USDA MyMarketNews API](https://mymarketnews.ams.usda.gov/mymarketnews-api)
- [Next.js Documentation](https://nextjs.org/docs)
- [Node.js Best Practices](https://github.com/goldbergyoni/nodebestpractices)

---
*Foodberg Technical Implementation*
*Version 2.0 - Chef-Focused Enhancement*
*Last Updated: 2025-10-11*