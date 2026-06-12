import { CheckCircle, Clock, Database, ExternalLink, FileText } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../services/api'

interface DataSourceInfo {
    id: string
    name: string
    description: string
    indicators: string[]
    update_frequency: string
    api_key_required: boolean
}

interface DatabaseStats {
    exists: boolean
    size_mb: number
}

interface SourceStatus {
    name: string
    records?: number
    // min/max are strings for date-keyed tables but NUMBERS (years) for
    // wasde_data — always coerce before formatting (a raw `.split()` on the
    // numeric year crashed the whole page render).
    date_range?: { min: string | number; max: string | number }
    freshness?: string
    error?: string
}

const fmtDate = (v: string | number | null | undefined): string | null =>
    v === null || v === undefined ? null : String(v).split(' ')[0]

export default function DataSources() {
    const [sources, setSources] = useState<DataSourceInfo[]>([])
    const [dbStats, setDbStats] = useState<DatabaseStats | null>(null)
    const [sourceStatus, setSourceStatus] = useState<{ [key: string]: SourceStatus }>({})
    const [_loading, setLoading] = useState(true)

    useEffect(() => {
        loadDataSources()
        loadDataStatus()
    }, [])

    const loadDataSources = async () => {
        try {
            const response = await api.getDataSources()
            setSources(response.data.sources || [])
        } catch (error) {
            console.error('Failed to load data sources:', error)
        }
    }

    const loadDataStatus = async () => {
        try {
            const response = await api.getDataStatus()
            const data = response.data
            setDbStats(data.database)
            setSourceStatus(data.sources || {})
        } catch (error) {
            console.error('Failed to load data status:', error)
        } finally {
            setLoading(false)
        }
    }

    const sourceDetails: { [key: string]: { url: string; logo?: string; description: string } } = {
        'wasde': {
            url: 'https://www.usda.gov/oce/commodity/wasde',
            description: 'The World Agricultural Supply and Demand Estimates (WASDE) report is published monthly by the USDA. It provides comprehensive forecasts of U.S. and world supply and demand for major crops and livestock products.'
        },
        'fred': {
            url: 'https://fred.stlouisfed.org/',
            description: 'Federal Reserve Economic Data (FRED) is a database of over 800,000 economic time series from 108 sources. We use FRED for Consumer Price Index (CPI) data and other economic indicators related to food prices.'
        },
        'bls': {
            url: 'https://www.bls.gov/',
            description: 'The Bureau of Labor Statistics provides detailed Consumer Price Index data, including food-specific indices that track price changes for various food categories over time.'
        },
        'fao': {
            url: 'https://www.fao.org/worldfoodsituation/foodpricesindex/en/',
            description: 'The FAO Food Price Index is a measure of the monthly change in international prices of a basket of food commodities. It has been published since 1990 and covers cereals, oilseeds, dairy, meat, and sugar.'
        },
        'worldbank': {
            url: 'https://data.worldbank.org/',
            description: 'The World Bank Open Data provides free access to global development data including agricultural production indices, food prices, and economic indicators across countries.'
        },
        'alphavantage': {
            url: 'https://www.alphavantage.co/',
            description: 'Alpha Vantage provides real-time and historical commodity price data including agricultural commodities like wheat, corn, soybeans, and sugar.'
        },
        'nass_history': {
            url: 'https://quickstats.nass.usda.gov/',
            description: 'USDA NASS Quick Stats full-history pull: prices received by farmers, production, and yield for ~50 commodities — national series back to 1908 (annual and monthly) and state series back to 1950 for the major commodities.'
        },
        'faostat': {
            url: 'https://www.fao.org/faostat/en/#data/PP',
            description: 'FAOSTAT bulk data: annual farm-gate producer prices in USD/tonne per country and food item (1991-present), plus monthly consumer food price indices (2015=100) for ~200 countries. Licensed CC-BY-4.0.'
        },
        'pinksheet': {
            url: 'https://www.worldbank.org/en/research/commodity-markets',
            description: 'The World Bank "Pink Sheet": monthly global commodity prices for ~45 commodities and the food/beverage/agriculture index families, 1960-present. Licensed CC-BY-4.0.'
        },
        'blsap': {
            url: 'https://www.bls.gov/cpi/average-prices/',
            description: 'BLS Average Price data: monthly US city-average retail prices for ~50 specific food products (eggs per dozen, milk per gallon, ground beef per pound...), most series since 1980.'
        }
    }

    // Derive the real DB status + last-updated from the fetched source freshness
    // (no hardcoded "Online"/"Today"). The freshest source with a max date drives
    // the overall status badge; its max date is the real "Last Updated".
    const FRESHNESS_LABEL: Record<string, { text: string; color: string }> = {
        fresh: { text: 'Fresh', color: 'text-emerald-400' },
        recent: { text: 'Recent', color: 'text-emerald-400' },
        stale: { text: 'Stale', color: 'text-amber-400' },
        outdated: { text: 'Outdated', color: 'text-red-400' },
        unknown: { text: 'Unknown', color: 'text-ark-fg-dim' },
    }
    const liveStatuses = Object.values(sourceStatus).filter((s) => !s.error)
    const latestStatus = liveStatuses.reduce<SourceStatus | null>((best, s) => {
        const d = fmtDate(s.date_range?.max)
        if (!d) return best
        if (!best || (fmtDate(best.date_range?.max) ?? '') < d) return s
        return best
    }, null)
    const lastUpdated = fmtDate(latestStatus?.date_range?.max)
    const overallFreshness = FRESHNESS_LABEL[latestStatus?.freshness ?? 'unknown'] ?? FRESHNESS_LABEL.unknown

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-ark-fg mb-2 flex items-center">
                    <Database className="w-8 h-8 mr-3 text-amber-400" />
                    Data Sources
                </h1>
                <p className="text-ark-fg-dim">
                    Learn about the data sources that power Foodberg's historical price database
                </p>
            </div>

            {/* Database Overview */}
            {dbStats && (
                <div className="card mb-8 bg-gradient-to-br from-emerald-900/20 to-emerald-800/10 border-emerald-700/30">
                    <h2 className="text-xl font-semibold text-emerald-400 mb-4">Database Overview</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        <div>
                            <div className="text-sm text-ark-fg-dim">Data Freshness</div>
                            <div className={`text-lg font-bold flex items-center ${overallFreshness.color}`}>
                                <CheckCircle className="w-5 h-5 mr-2" />
                                {overallFreshness.text}
                            </div>
                        </div>
                        <div>
                            <div className="text-sm text-ark-fg-dim">Database Size</div>
                            <div className="text-lg font-bold text-ark-fg">{dbStats.size_mb.toFixed(1)} MB</div>
                        </div>
                        <div>
                            <div className="text-sm text-ark-fg-dim">Data Sources</div>
                            <div className="text-lg font-bold text-ark-fg">{sources.length}</div>
                        </div>
                        <div>
                            <div className="text-sm text-ark-fg-dim">Last Updated</div>
                            <div className="text-lg font-bold text-ark-fg flex items-center">
                                <Clock className="w-4 h-4 mr-2" />
                                {lastUpdated ?? 'Unknown'}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Source Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {sources.map((source) => {
                    const details = sourceDetails[source.id] || {}
                    // Map each source to the DB table that actually backs it, so the
                    // "Records in Database" stat is real (World Bank prices live in the
                    // global_prices table alongside FAO, not in economic_indicators).
                    const statusKey = (source.id === 'wasde' || source.id === 'nass_history') ? 'wasde_data'
                        : (source.id === 'fao' || source.id === 'worldbank' || source.id === 'faostat' || source.id === 'pinksheet') ? 'global_prices'
                            : source.id === 'blsap' ? 'retail_prices'
                                : 'economic_indicators'
                    const status = sourceStatus[statusKey]

                    return (
                        <div key={source.id} className="card">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="text-xl font-semibold text-ark-fg">{source.name}</h3>
                                    <span className="text-sm text-ark-fg-dim">{source.update_frequency}</span>
                                </div>
                                {details.url && (
                                    <a
                                        href={details.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-emerald-400 hover:text-emerald-300 transition-colors"
                                    >
                                        <ExternalLink className="w-5 h-5" />
                                    </a>
                                )}
                            </div>

                            <p className="text-ark-fg-dim text-sm mb-4">
                                {details.description || source.description}
                            </p>

                            <div className="mb-4">
                                <div className="text-sm text-ark-fg-dim mb-2">Available Indicators:</div>
                                <div className="flex flex-wrap gap-2">
                                    {source.indicators.slice(0, 5).map((indicator) => (
                                        <span
                                            key={indicator}
                                            className="px-2 py-1 bg-ark-tag text-ark-fg-dim text-xs rounded"
                                        >
                                            {indicator}
                                        </span>
                                    ))}
                                    {source.indicators.length > 5 && (
                                        <span className="px-2 py-1 bg-ark-tag text-ark-fg-dim text-xs rounded">
                                            +{source.indicators.length - 5} more
                                        </span>
                                    )}
                                </div>
                            </div>

                            {status && !status.error && (
                                <div className="pt-4 border-t border-ark-line">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-ark-fg-dim">Records in Database:</span>
                                        <span className="text-ark-fg font-medium">
                                            {status.records?.toLocaleString() || 'N/A'}
                                        </span>
                                    </div>
                                    {status.date_range && (
                                        <div className="flex justify-between text-sm mt-1">
                                            <span className="text-ark-fg-dim">Date Range:</span>
                                            <span className="text-ark-fg">
                                                {fmtDate(status.date_range.min)} to {fmtDate(status.date_range.max)}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            )}

                            <div className="mt-4 flex items-center text-xs">
                                {source.api_key_required ? (
                                    <span className="text-amber-400">Requires API Key</span>
                                ) : (
                                    <span className="text-emerald-400">Public API</span>
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>

            {/* Methodology Section */}
            <div className="card">
                <h2 className="text-xl font-semibold text-ark-fg mb-4 flex items-center">
                    <FileText className="w-5 h-5 mr-2 text-ark-fg-dim" />
                    Data Methodology
                </h2>
                <div className="max-w-none">
                    <div className="space-y-4 text-ark-fg-dim">
                        <p>
                            Foodberg aggregates food commodity price data from multiple authoritative sources to provide
                            a comprehensive view of historical food prices. Our data collection follows these principles:
                        </p>

                        <h3 className="text-lg font-semibold text-ark-fg mt-6">Data Collection</h3>
                        <ul className="list-disc list-inside space-y-2 text-ark-fg-dim">
                            <li>Data is collected from official government and international organization sources</li>
                            <li>We preserve original values and units without transformation</li>
                            <li>Each data point includes source attribution and collection timestamp</li>
                            <li>Historical data is maintained to allow for long-term trend analysis</li>
                        </ul>

                        <h3 className="text-lg font-semibold text-ark-fg mt-6">Data Updates</h3>
                        <ul className="list-disc list-inside space-y-2 text-ark-fg-dim">
                            <li>WASDE reports are released monthly (usually around the 10th)</li>
                            <li>FAO Food Price Index is updated monthly</li>
                            <li>BLS CPI data is released monthly</li>
                            <li>Alpha Vantage commodity data is available daily</li>
                        </ul>

                        <h3 className="text-lg font-semibold text-ark-fg mt-6">Limitations</h3>
                        <ul className="list-disc list-inside space-y-2 text-ark-fg-dim">
                            <li>This tool is for historical research and educational purposes only</li>
                            <li>We do not provide price forecasts or predictions</li>
                            <li>Data may have a delay of several hours to days depending on the source</li>
                            <li>Different sources may use different methodologies and definitions</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    )
}
