import { BarChart3, History, Layers, TrendingUp } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../services/api'
import {
    Area,
    CartesianGrid,
    ComposedChart,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis
} from 'recharts'

// Color palette for multiple commodities
const COLORS = [
    '#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
]

export default function HistoricalTrends() {
    const [selectedCommodities, setSelectedCommodities] = useState<string[]>(['wheat', 'corn'])
    const [chartData, setChartData] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [timeRange, setTimeRange] = useState<string>('all')
    const [chartType, setChartType] = useState<'line' | 'area' | 'normalized'>('line')

    const availableCommodities = [
        { id: 'wheat', name: 'Wheat', category: 'Grains' },
        { id: 'corn', name: 'Corn', category: 'Grains' },
        { id: 'rice', name: 'Rice', category: 'Grains' },
        { id: 'soybeans', name: 'Soybeans', category: 'Oilseeds' },
        { id: 'cotton', name: 'Cotton', category: 'Fiber' },
        { id: 'cattle', name: 'Cattle', category: 'Livestock' },
        { id: 'hogs', name: 'Hogs', category: 'Livestock' },
        { id: 'milk', name: 'Milk', category: 'Dairy' },
        { id: 'eggs', name: 'Eggs', category: 'Dairy' },
        { id: 'chickens', name: 'Chickens', category: 'Livestock' },
    ]

    useEffect(() => {
        loadMultiCommodityData()
    }, [selectedCommodities, timeRange])

    const loadMultiCommodityData = async () => {
        if (selectedCommodities.length === 0) {
            setChartData([])
            return
        }

        setLoading(true)
        try {
            // Fetch data for all selected commodities in parallel
            const promises = selectedCommodities.map(async (commodity) => {
                const response = await api.getWASDEData(commodity, 5000)
                return { commodity, data: response.data.data || [] }
            })

            const results = await Promise.all(promises)

            // Combine data by year
            const yearlyData: { [year: number]: any } = {}

            results.forEach(({ commodity, data }) => {
                // Group by year
                const commodityByYear: { [year: number]: number[] } = {}
                data.forEach((record: any) => {
                    if (record.numeric_value !== null) {
                        if (!commodityByYear[record.year]) {
                            commodityByYear[record.year] = []
                        }
                        commodityByYear[record.year].push(record.numeric_value)
                    }
                })

                // Average values per year
                Object.entries(commodityByYear).forEach(([year, values]) => {
                    const yearNum = parseInt(year)
                    if (!yearlyData[yearNum]) {
                        yearlyData[yearNum] = { year: yearNum }
                    }
                    yearlyData[yearNum][commodity] = values.reduce((a, b) => a + b, 0) / values.length
                })
            })

            // Convert to array and filter by time range
            let chartArray = Object.values(yearlyData).sort((a, b) => a.year - b.year)

            if (timeRange !== 'all') {
                const years = parseInt(timeRange)
                const currentYear = new Date().getFullYear()
                chartArray = chartArray.filter((d: any) => d.year >= currentYear - years)
            }

            // Normalize if needed
            if (chartType === 'normalized' && chartArray.length > 0) {
                const baselineYear = chartArray[0]
                chartArray = chartArray.map((d: any) => {
                    const normalized: any = { year: d.year }
                    selectedCommodities.forEach(commodity => {
                        if (d[commodity] !== undefined && baselineYear[commodity]) {
                            normalized[commodity] = (d[commodity] / baselineYear[commodity]) * 100
                        }
                    })
                    return normalized
                })
            }

            setChartData(chartArray)
        } catch (error) {
            console.error('Failed to load commodity data:', error)
        } finally {
            setLoading(false)
        }
    }

    const toggleCommodity = (commodityId: string) => {
        if (selectedCommodities.includes(commodityId)) {
            setSelectedCommodities(selectedCommodities.filter(c => c !== commodityId))
        } else if (selectedCommodities.length < 6) {
            setSelectedCommodities([...selectedCommodities, commodityId])
        }
    }

    // Calculate correlations between commodities
    const calculateCorrelation = (data: any[], key1: string, key2: string): number => {
        const pairs = data.filter(d => d[key1] !== undefined && d[key2] !== undefined)
        if (pairs.length < 2) return 0

        const n = pairs.length
        const sum1 = pairs.reduce((s, d) => s + d[key1], 0)
        const sum2 = pairs.reduce((s, d) => s + d[key2], 0)
        const sum1Sq = pairs.reduce((s, d) => s + d[key1] * d[key1], 0)
        const sum2Sq = pairs.reduce((s, d) => s + d[key2] * d[key2], 0)
        const pSum = pairs.reduce((s, d) => s + d[key1] * d[key2], 0)

        const num = pSum - (sum1 * sum2 / n)
        const den = Math.sqrt((sum1Sq - sum1 * sum1 / n) * (sum2Sq - sum2 * sum2 / n))

        return den === 0 ? 0 : num / den
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-slate-100 mb-2 flex items-center">
                    <History className="w-8 h-8 mr-3 text-purple-400" />
                    Historical Trends
                </h1>
                <p className="text-slate-400">
                    Compare long-term price trends across multiple commodities
                </p>
            </div>

            {/* Commodity Selector */}
            <div className="card mb-6">
                <h2 className="text-lg font-semibold text-slate-100 mb-4">
                    Select Commodities to Compare
                    <span className="text-sm text-slate-400 ml-2">
                        ({selectedCommodities.length}/6 selected)
                    </span>
                </h2>
                <div className="flex flex-wrap gap-2">
                    {availableCommodities.map((commodity) => (
                        <button
                            key={commodity.id}
                            onClick={() => toggleCommodity(commodity.id)}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${selectedCommodities.includes(commodity.id)
                                ? 'text-white'
                                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                }`}
                            style={selectedCommodities.includes(commodity.id) ? {
                                backgroundColor: COLORS[selectedCommodities.indexOf(commodity.id) % COLORS.length]
                            } : {}}
                            disabled={!selectedCommodities.includes(commodity.id) && selectedCommodities.length >= 6}
                        >
                            {commodity.name}
                        </button>
                    ))}
                </div>
            </div>

            {/* Chart Controls */}
            <div className="card mb-6">
                <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                    <div>
                        <label className="block text-sm text-slate-400 mb-2">Time Range</label>
                        <div className="flex gap-2">
                            {[
                                { value: '5', label: '5 Years' },
                                { value: '10', label: '10 Years' },
                                { value: '20', label: '20 Years' },
                                { value: 'all', label: 'All Time' }
                            ].map(option => (
                                <button
                                    key={option.value}
                                    onClick={() => setTimeRange(option.value)}
                                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${timeRange === option.value
                                        ? 'bg-emerald-600 text-white'
                                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                        }`}
                                >
                                    {option.label}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm text-slate-400 mb-2">Chart Type</label>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setChartType('line')}
                                className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center ${chartType === 'line'
                                    ? 'bg-emerald-600 text-white'
                                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                    }`}
                            >
                                <TrendingUp className="w-4 h-4 mr-2" />
                                Line
                            </button>
                            <button
                                onClick={() => setChartType('area')}
                                className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center ${chartType === 'area'
                                    ? 'bg-emerald-600 text-white'
                                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                    }`}
                            >
                                <Layers className="w-4 h-4 mr-2" />
                                Area
                            </button>
                            <button
                                onClick={() => setChartType('normalized')}
                                className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center ${chartType === 'normalized'
                                    ? 'bg-emerald-600 text-white'
                                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                    }`}
                            >
                                <BarChart3 className="w-4 h-4 mr-2" />
                                Normalized
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Chart */}
            <div className="card mb-6">
                <h2 className="text-xl font-semibold text-slate-100 mb-4">
                    {chartType === 'normalized' ? 'Normalized Price Trends (Base Year = 100)' : 'Historical Price Comparison'}
                </h2>

                {loading ? (
                    <div className="h-[500px] flex items-center justify-center">
                        <div className="text-center">
                            <div className="animate-spin w-12 h-12 border-2 border-emerald-400 border-t-transparent rounded-full mx-auto"></div>
                            <p className="text-slate-400 mt-4">Loading price data...</p>
                        </div>
                    </div>
                ) : chartData.length > 0 ? (
                    <div className="h-[500px]">
                        <ResponsiveContainer width="100%" height="100%">
                            {chartType === 'area' ? (
                                <ComposedChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                    <XAxis
                                        dataKey="year"
                                        stroke="#9CA3AF"
                                        tick={{ fill: '#9CA3AF' }}
                                    />
                                    <YAxis
                                        stroke="#9CA3AF"
                                        tick={{ fill: '#9CA3AF' }}
                                        tickFormatter={(value) => value.toLocaleString()}
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: '#1E293B',
                                            border: '1px solid #374151',
                                            borderRadius: '8px'
                                        }}
                                        labelStyle={{ color: '#F1F5F9' }}
                                        formatter={(value: number, name: string) => [
                                            value.toLocaleString(undefined, { maximumFractionDigits: 2 }),
                                            name.charAt(0).toUpperCase() + name.slice(1)
                                        ]}
                                    />
                                    <Legend />
                                    {selectedCommodities.map((commodity, index) => (
                                        <Area
                                            key={commodity}
                                            type="monotone"
                                            dataKey={commodity}
                                            name={commodity.charAt(0).toUpperCase() + commodity.slice(1)}
                                            stroke={COLORS[index % COLORS.length]}
                                            fill={COLORS[index % COLORS.length]}
                                            fillOpacity={0.2}
                                            strokeWidth={2}
                                        />
                                    ))}
                                </ComposedChart>
                            ) : (
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                    <XAxis
                                        dataKey="year"
                                        stroke="#9CA3AF"
                                        tick={{ fill: '#9CA3AF' }}
                                    />
                                    <YAxis
                                        stroke="#9CA3AF"
                                        tick={{ fill: '#9CA3AF' }}
                                        tickFormatter={(value) => chartType === 'normalized'
                                            ? `${value.toFixed(0)}%`
                                            : value.toLocaleString()
                                        }
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: '#1E293B',
                                            border: '1px solid #374151',
                                            borderRadius: '8px'
                                        }}
                                        labelStyle={{ color: '#F1F5F9' }}
                                        formatter={(value: number, name: string) => [
                                            chartType === 'normalized'
                                                ? `${value.toFixed(1)}%`
                                                : value.toLocaleString(undefined, { maximumFractionDigits: 2 }),
                                            name.charAt(0).toUpperCase() + name.slice(1)
                                        ]}
                                    />
                                    <Legend />
                                    {selectedCommodities.map((commodity, index) => (
                                        <Line
                                            key={commodity}
                                            type="monotone"
                                            dataKey={commodity}
                                            name={commodity.charAt(0).toUpperCase() + commodity.slice(1)}
                                            stroke={COLORS[index % COLORS.length]}
                                            strokeWidth={2}
                                            dot={false}
                                            activeDot={{ r: 6 }}
                                        />
                                    ))}
                                </LineChart>
                            )}
                        </ResponsiveContainer>
                    </div>
                ) : (
                    <div className="h-[500px] flex items-center justify-center text-slate-400">
                        <div className="text-center">
                            <History className="w-16 h-16 mx-auto mb-4 text-slate-600" />
                            <p>Select commodities to compare their price trends</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Correlation Matrix */}
            {selectedCommodities.length >= 2 && chartData.length > 0 && (
                <div className="card">
                    <h2 className="text-xl font-semibold text-slate-100 mb-4">Price Correlations</h2>
                    <p className="text-slate-400 text-sm mb-4">
                        Shows how closely commodity prices move together. +1 = perfect positive correlation, -1 = perfect negative correlation.
                    </p>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr>
                                    <th className="text-left p-2 text-slate-400"></th>
                                    {selectedCommodities.map(c => (
                                        <th key={c} className="p-2 text-slate-300 capitalize">{c}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {selectedCommodities.map((c1, i) => (
                                    <tr key={c1}>
                                        <td className="p-2 text-slate-300 capitalize font-medium">{c1}</td>
                                        {selectedCommodities.map((c2, j) => {
                                            const correlation = i === j ? 1 : calculateCorrelation(chartData, c1, c2)
                                            const bgColor = correlation > 0.7 ? 'bg-green-900/30' :
                                                correlation > 0.3 ? 'bg-green-900/10' :
                                                    correlation < -0.3 ? 'bg-red-900/10' :
                                                        correlation < -0.7 ? 'bg-red-900/30' : ''
                                            return (
                                                <td key={c2} className={`p-2 text-center ${bgColor}`}>
                                                    <span className={correlation > 0.5 ? 'text-green-400' : correlation < -0.5 ? 'text-red-400' : 'text-slate-400'}>
                                                        {correlation.toFixed(2)}
                                                    </span>
                                                </td>
                                            )
                                        })}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}
