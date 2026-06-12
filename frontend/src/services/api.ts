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
    getPriceHistory: (commodity: string) =>
        apiClient.get(`/api/prices/history/${commodity}`),
    getSourceHistory: (commodity: string, source: string) =>
        apiClient.get(`/api/prices/source/${commodity}`, { params: { source } }),

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
}

// Absolute URL for a download file (CSV/Parquet/dictionary). Used directly as
// an <a href> so the browser streams the attachment without going through axios.
export const downloadUrl = (path: string): string => {
    const base = (API_URL || '').replace(/\/$/, '')
    return path.startsWith('http') ? path : `${base}${path}`
}

export default apiClient
