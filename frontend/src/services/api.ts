import axios from 'axios'

// Default = same-origin relative ('' + '/api/...') so production builds work
// behind the Caddy proxy with NO build-time env. Local dev sets VITE_API_URL
// in .env.development (the old 'http://localhost:8002' fallback shipped to
// production once and killed every data view for visitors).
const API_URL = import.meta.env.VITE_API_URL || ''

const apiClient = axios.create({
    baseURL: API_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
})

// API methods
export const api = {
    // Health check
    health: () => apiClient.get('/api/health'),

    // Database stats
    getDatabaseStats: () => apiClient.get('/api/prices/database/stats'),

    // Data sources and status
    getDataSources: () => apiClient.get('/api/data/sources'),
    getDataStatus: () => apiClient.get('/api/data/status'),

    // WASDE commodities
    getWASDECommodities: () => apiClient.get('/api/wasde/commodities'),
    getWASDEData: (commodity: string, limit = 5000) =>
        apiClient.get(`/api/wasde/${commodity}`, { params: { limit } }),
    getWASDENational: (commodity: string) =>
        apiClient.get(`/api/wasde/${commodity}/national`),
    getWASDEState: (commodity: string, state: string) =>
        apiClient.get(`/api/wasde/${commodity}/state/${state}`),

    // Price endpoints
    getTerminalPrices: (market = 'new_york', date?: string) =>
        apiClient.get(`/api/prices/terminal/${market}`, { params: { date } }),
    searchPrices: (commodity: string, sources = 'wasde', params?: Record<string, string>) =>
        apiClient.get('/api/prices/search', { params: { commodity, sources, ...params } }),
    getPriceTrend: (commodity: string, period = '6months', source = 'wasde') =>
        apiClient.get(`/api/prices/trend/${commodity}`, { params: { period, source } }),
    getPriceStats: (commodity: string, source = 'wasde') =>
        apiClient.get(`/api/prices/stats/${commodity}`, { params: { source } }),

    // Economic indicators
    getEconomicIndicators: () => apiClient.get('/api/economic/indicators'),

    // Global data
    getFAOIndex: (category = 'overall') =>
        apiClient.get('/api/global/fao-index', { params: { category } }),
    getWorldBankCommodity: (commodity: string) =>
        apiClient.get(`/api/global/worldbank/${commodity}`),

    // Composite indices
    getCompositeIndices: () => apiClient.get('/api/indices/'),
    getCompositeIndex: (category: string) =>
        apiClient.get(`/api/indices/${category}`),

    // Real price-history coverage (which commodities have a genuine series)
    getPriceCoverage: () => apiClient.get('/api/prices/coverage'),

    // The detail rail behind the Price Explorer: every source carrying an item
    // (with a normalized frequency and a last-real-observation date), its
    // regional variants, the farm -> wholesale -> retail wedge where all three
    // genuinely exist, and inline provenance.
    getPriceDetail: (slug: string) =>
        apiClient.get(`/api/prices/detail/${encodeURIComponent(slug)}`),

    // GDP implicit price deflator, for the client-side real-terms toggle.
    // WEBSITE_VISUALIZATION_STANDARD §2 requires the GDP deflator and forbids
    // CPI — deflating a food price by an index containing food prices is
    // circular. Returns an honest data_unavailable payload rather than a 500
    // when the series has not been ingested.
    getDeflator: () => apiClient.get('/api/prices/deflator'),
    getPriceHistory: (commodity: string) =>
        apiClient.get(`/api/prices/history/${commodity}`),
    getSourceHistory: (commodity: string, source: string) =>
        apiClient.get(`/api/prices/source/${commodity}`, { params: { source } }),

    // USDA AMS Market News — daily terminal-market wholesale prices.
    // The only source on the site with daily cadence and chef-level granularity
    // (variety x package x grade x origin x organic), so rows are never averaged.
    getWholesaleMarkets: () => apiClient.get('/api/wholesale/markets'),
    getWholesaleCommodities: (city?: string) =>
        apiClient.get('/api/wholesale/commodities', { params: city ? { city } : {} }),
    searchWholesale: (params: Record<string, string | number | undefined>) =>
        apiClient.get('/api/wholesale/search', { params }),

    // Geographic comparison (World Bank indicators, per-region annual series)
    getGeoIndicators: () => apiClient.get('/api/geo/indicators'),
    getGeoSeries: (indicatorCode: string) =>
        apiClient.get(`/api/geo/${indicatorCode}`),
    getProducerItems: () => apiClient.get('/api/geo/producer/items'),
    getProducerSeries: (item: string) =>
        apiClient.get(`/api/geo/producer/${encodeURIComponent(item)}`),
    getStateSeries: (commodity: string) =>
        apiClient.get(`/api/geo/states/${commodity}`),

    // Global index families (Pink Sheet indices, FAO country food CPIs)
    getGlobalIndices: () => apiClient.get('/api/indices/global'),
    getCountryCpi: (country: string) =>
        apiClient.get(`/api/indices/cpi/${encodeURIComponent(country)}`),
    getPinksheetSeries: (series: string) =>
        apiClient.get(`/api/indices/pinksheet/${encodeURIComponent(series)}`),

    // Bulk dataset downloads
    getDownloadDatasets: () => apiClient.get('/api/download/datasets'),

    // WASDE Vintages — as-reported revision trajectory per report date
    getVintagesCommodities: () => apiClient.get('/api/vintages/commodities'),
    getVintagesAttributes: (commodity: string) =>
        apiClient.get(`/api/vintages/${encodeURIComponent(commodity)}/attributes`),
    getVintagesSeries: (commodity: string, attribute: string, region: string, marketYear: string) =>
        apiClient.get(`/api/vintages/${encodeURIComponent(commodity)}/series`, {
            params: { attribute, region, market_year: marketYear },
        }),
    getVintagesMarketYears: (commodity: string) =>
        apiClient.get(`/api/vintages/${encodeURIComponent(commodity)}/market-years`),

    // WASDE Legacy — machine-extracted historical WASDE (1979–2009)
    getLegacyCommodities: () => apiClient.get('/api/legacy/commodities'),
    getLegacyCoverage: () => apiClient.get('/api/legacy/coverage'),
    getLegacySeries: (commodity: string, region: string, attribute?: string) =>
        apiClient.get(`/api/legacy/${encodeURIComponent(commodity)}/series`, {
            params: { region, ...(attribute ? { attribute } : {}) },
        }),

    // Admin: trigger server-side data reindex (rebuild indices/caches)
    reindex: () => apiClient.post('/api/data/reindex'),

    // WASDE Supply & Demand (USDA FAS PS&D, marketing-year 1960→present)
    getPsdCommodities: () => apiClient.get('/api/psd/commodities'),
    getPsdAttributes: (commodity: string, region = 'World') =>
        apiClient.get(`/api/psd/${encodeURIComponent(commodity)}/attributes`, { params: { region } }),
    getPsdSeries: (commodity: string, attribute: string, region = 'World') =>
        apiClient.get(`/api/psd/${encodeURIComponent(commodity)}/series`, { params: { attribute, region } }),
    getPsdBalanceSheet: (commodity: string, region = 'World', year?: number) =>
        apiClient.get(`/api/psd/${encodeURIComponent(commodity)}/balance-sheet`, { params: { region, year } }),
}

// Absolute URL for a download file (CSV/Parquet/dictionary). Used directly as
// an <a href> so the browser streams the attachment without going through axios.
export const downloadUrl = (path: string): string => {
    const base = (API_URL || '').replace(/\/$/, '')
    return path.startsWith('http') ? path : `${base}${path}`
}

export default apiClient
