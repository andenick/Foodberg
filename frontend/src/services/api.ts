import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
}

export default apiClient
