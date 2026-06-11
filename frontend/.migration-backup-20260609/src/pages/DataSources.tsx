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
    date_range?: { min: string; max: string }
    freshness?: string
    error?: string
}

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
        }
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-slate-100 mb-2 flex items-center">
                    <Database className="w-8 h-8 mr-3 text-amber-400" />
                    Data Sources
                </h1>
                <p className="text-slate-400">
                    Learn about the data sources that power Foodberg's historical price database
                </p>
            </div>

            {/* Database Overview */}
            {dbStats && (
                <div className="card mb-8 bg-gradient-to-br from-emerald-900/20 to-emerald-800/10 border-emerald-700/30">
                    <h2 className="text-xl font-semibold text-emerald-400 mb-4">Database Overview</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        <div>
                            <div className="text-sm text-slate-400">Status</div>
                            <div className="text-lg font-bold text-emerald-400 flex items-center">
                                <CheckCircle className="w-5 h-5 mr-2" />
                                Online
                            </div>
                        </div>
                        <div>
                            <div className="text-sm text-slate-400">Database Size</div>
                            <div className="text-lg font-bold text-slate-100">{dbStats.size_mb.toFixed(1)} MB</div>
                        </div>
                        <div>
                            <div className="text-sm text-slate-400">Data Sources</div>
                            <div className="text-lg font-bold text-slate-100">{sources.length}</div>
                        </div>
                        <div>
                            <div className="text-sm text-slate-400">Last Updated</div>
                            <div className="text-lg font-bold text-slate-100 flex items-center">
                                <Clock className="w-4 h-4 mr-2" />
                                Today
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Source Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {sources.map((source) => {
                    const details = sourceDetails[source.id] || {}
                    const status = sourceStatus[source.id === 'wasde' ? 'wasde_data' :
                        source.id === 'fao' ? 'global_prices' :
                            'economic_indicators']

                    return (
                        <div key={source.id} className="card">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="text-xl font-semibold text-slate-100">{source.name}</h3>
                                    <span className="text-sm text-slate-400">{source.update_frequency}</span>
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

                            <p className="text-slate-400 text-sm mb-4">
                                {details.description || source.description}
                            </p>

                            <div className="mb-4">
                                <div className="text-sm text-slate-500 mb-2">Available Indicators:</div>
                                <div className="flex flex-wrap gap-2">
                                    {source.indicators.slice(0, 5).map((indicator) => (
                                        <span
                                            key={indicator}
                                            className="px-2 py-1 bg-slate-700 text-slate-300 text-xs rounded"
                                        >
                                            {indicator}
                                        </span>
                                    ))}
                                    {source.indicators.length > 5 && (
                                        <span className="px-2 py-1 bg-slate-700 text-slate-400 text-xs rounded">
                                            +{source.indicators.length - 5} more
                                        </span>
                                    )}
                                </div>
                            </div>

                            {status && !status.error && (
                                <div className="pt-4 border-t border-slate-700">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-400">Records in Database:</span>
                                        <span className="text-slate-200 font-medium">
                                            {status.records?.toLocaleString() || 'N/A'}
                                        </span>
                                    </div>
                                    {status.date_range && (
                                        <div className="flex justify-between text-sm mt-1">
                                            <span className="text-slate-400">Date Range:</span>
                                            <span className="text-slate-200">
                                                {status.date_range.min?.split(' ')[0]} to {status.date_range.max?.split(' ')[0]}
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
                <h2 className="text-xl font-semibold text-slate-100 mb-4 flex items-center">
                    <FileText className="w-5 h-5 mr-2 text-slate-400" />
                    Data Methodology
                </h2>
                <div className="prose prose-invert prose-slate max-w-none">
                    <div className="space-y-4 text-slate-300">
                        <p>
                            Foodberg aggregates food commodity price data from multiple authoritative sources to provide
                            a comprehensive view of historical food prices. Our data collection follows these principles:
                        </p>

                        <h3 className="text-lg font-semibold text-slate-100 mt-6">Data Collection</h3>
                        <ul className="list-disc list-inside space-y-2 text-slate-400">
                            <li>Data is collected from official government and international organization sources</li>
                            <li>We preserve original values and units without transformation</li>
                            <li>Each data point includes source attribution and collection timestamp</li>
                            <li>Historical data is maintained to allow for long-term trend analysis</li>
                        </ul>

                        <h3 className="text-lg font-semibold text-slate-100 mt-6">Data Updates</h3>
                        <ul className="list-disc list-inside space-y-2 text-slate-400">
                            <li>WASDE reports are released monthly (usually around the 10th)</li>
                            <li>FAO Food Price Index is updated monthly</li>
                            <li>BLS CPI data is released monthly</li>
                            <li>Alpha Vantage commodity data is available daily</li>
                        </ul>

                        <h3 className="text-lg font-semibold text-slate-100 mt-6">Limitations</h3>
                        <ul className="list-disc list-inside space-y-2 text-slate-400">
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
