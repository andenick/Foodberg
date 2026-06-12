import { History } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../services/api'
import {
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis
} from 'recharts'
import { useArkTheme } from '../arcanum/arkChartTheme'
import { ChartMetaStrip, ScrollableDataTable } from '../components/ChartDetails'

// Color palette for multiple commodities
const COLORS = [
    '#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
]

/* The comparison picker offers ONLY commodities with a genuine monthly price
   series in the local dataset (Alpha Vantage, 1992-present). Everything else
   has a single WASDE marketing year — one point is not a trend, so it is not
   offered here (see the Price Explorer for those values). */
const HISTORY_COMMODITIES = [
    { id: 'wheat', name: 'Wheat' },
    { id: 'corn', name: 'Corn' },
    { id: 'coffee', name: 'Coffee' },
    { id: 'sugar', name: 'Sugar' },
    { id: 'cotton', name: 'Cotton' },
]

export default function HistoricalTrends() {
    const [selectedCommodities, setSelectedCommodities] = useState<string[]>(['wheat', 'corn'])
    const [chartData, setChartData] = useState<any[]>([])
    const [units, setUnits] = useState<Record<string, string>>({})
    const [loading, setLoading] = useState(true)
    const [timeRange, setTimeRange] = useState<string>('all')
    const t = useArkTheme()

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
            const results = await Promise.all(
                selectedCommodities.map(async (commodity) => {
                    const response = await api.getPriceHistory(commodity)
                    return { commodity, payload: response.data }
                })
            )

            const nextUnits: Record<string, string> = {}
            const yearlyData: { [year: number]: any } = {}

            results.forEach(({ commodity, payload }) => {
                if (!payload.has_history) return
                nextUnits[commodity] = payload.unit || 'USD'
                const byYear: { [year: number]: number[] } = {}
                for (const row of payload.data || []) {
                    if (row.price !== null && row.price !== undefined) {
                        (byYear[row.year] ||= []).push(row.price)
                    }
                }
                Object.entries(byYear).forEach(([year, values]) => {
                    const y = Number(year)
                    yearlyData[y] ||= { year: y }
                    yearlyData[y][commodity] = values.reduce((a, b) => a + b, 0) / values.length
                })
            })

            let chartArray = Object.values(yearlyData).sort((a: any, b: any) => a.year - b.year)
            if (timeRange !== 'all') {
                const years = parseInt(timeRange)
                const currentYear = new Date().getFullYear()
                chartArray = chartArray.filter((d: any) => d.year >= currentYear - years)
            }

            setUnits(nextUnits)
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
        } else if (selectedCommodities.length < 5) {
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

    const yearSpan = chartData.length
        ? `${chartData[0].year}–${chartData[chartData.length - 1].year}`
        : null

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-ark-fg mb-2 flex items-center">
                    <History className="w-8 h-8 mr-3 text-purple-400" />
                    Historical Trends
                </h1>
                <p className="text-ark-fg-dim">
                    Compare long-term price trends across the five commodities with genuine
                    monthly history in the local dataset (Alpha Vantage spot prices, 1992–present,
                    plotted as annual averages). Other commodities carry only a single WASDE
                    marketing year and cannot show a trend.
                </p>
            </div>

            {/* Commodity Selector */}
            <div className="card mb-6">
                <h2 className="text-lg font-semibold text-ark-fg mb-4">
                    Select Commodities to Compare
                    <span className="text-sm text-ark-fg-dim ml-2">
                        ({selectedCommodities.length}/{HISTORY_COMMODITIES.length} selected)
                    </span>
                </h2>
                <div className="flex flex-wrap gap-2">
                    {HISTORY_COMMODITIES.map((commodity) => (
                        <button
                            key={commodity.id}
                            onClick={() => toggleCommodity(commodity.id)}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${selectedCommodities.includes(commodity.id)
                                ? 'text-white'
                                : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                }`}
                            style={selectedCommodities.includes(commodity.id) ? {
                                backgroundColor: COLORS[selectedCommodities.indexOf(commodity.id) % COLORS.length]
                            } : {}}
                        >
                            {commodity.name}
                        </button>
                    ))}
                </div>
            </div>

            {/* Time range */}
            <div className="card mb-6">
                <label className="block text-sm text-ark-fg-dim mb-2">Time Range</label>
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
                                : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                }`}
                        >
                            {option.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Main Chart */}
            <div className="card mb-6">
                <h2 className="text-xl font-semibold text-ark-fg mb-4">Historical Price Comparison</h2>

                {loading ? (
                    <div className="h-[500px] flex items-center justify-center">
                        <div className="text-center">
                            <div className="animate-spin w-12 h-12 border-2 border-emerald-400 border-t-transparent rounded-full mx-auto"></div>
                            <p className="text-ark-fg-dim mt-4">Loading price data...</p>
                        </div>
                    </div>
                ) : chartData.length > 0 ? (
                    <>
                        <div className="h-[500px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData} margin={{ left: 12, bottom: 8 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={t.gridStroke} />
                                    <XAxis
                                        dataKey="year"
                                        stroke={t.axisStroke}
                                        tick={{ fill: t.dim }}
                                        label={{ value: 'Year', position: 'insideBottom', offset: -4, fill: t.dim, fontSize: 12 }}
                                    />
                                    <YAxis
                                        stroke={t.axisStroke}
                                        tick={{ fill: t.dim }}
                                        tickFormatter={(value) => value.toLocaleString()}
                                        label={{ value: 'USD (annual average, per-unit basis varies)', angle: -90, position: 'insideLeft', fill: t.dim, fontSize: 11 }}
                                    />
                                    <Tooltip
                                        contentStyle={t.tooltip}
                                        labelStyle={{ color: t.fg }}
                                        formatter={(value: number, name: string) => [
                                            `${value.toLocaleString(undefined, { maximumFractionDigits: 2 })} ${units[name] || ''}`,
                                            name.charAt(0).toUpperCase() + name.slice(1)
                                        ]}
                                        labelFormatter={(label) => `Year ${label}`}
                                    />
                                    <Legend formatter={(v: string) => v.charAt(0).toUpperCase() + v.slice(1)} />
                                    {selectedCommodities.map((commodity, index) => (
                                        <Line
                                            key={commodity}
                                            type="monotone"
                                            dataKey={commodity}
                                            name={commodity}
                                            stroke={COLORS[index % COLORS.length]}
                                            strokeWidth={2}
                                            dot={false}
                                            activeDot={{ r: 6 }}
                                            connectNulls
                                        />
                                    ))}
                                </LineChart>
                            </ResponsiveContainer>
                        </div>

                        <ChartMetaStrip
                            meta={{
                                source: 'Alpha Vantage monthly spot prices (local dataset, offline)',
                                unit: selectedCommodities.map(c => `${c}: ${units[c] || '—'}`).join(' · '),
                                dateRange: yearSpan,
                                points: chartData.length,
                                note: 'Each point is the average of that year\'s monthly observations. Units differ per commodity — compare shapes, not levels.',
                            }}
                        />

                        <ScrollableDataTable
                            rows={chartData}
                            columns={[
                                { key: 'year', label: 'Year' },
                                ...selectedCommodities.map(c => ({ key: c, label: c.charAt(0).toUpperCase() + c.slice(1), numeric: true })),
                            ]}
                            filename="foodberg_trends"
                        />
                    </>
                ) : (
                    <div className="h-[500px] flex items-center justify-center text-ark-fg-dim">
                        <div className="text-center">
                            <History className="w-16 h-16 mx-auto mb-4 text-ark-fg-dim" />
                            <p>Select commodities to compare their price trends</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Correlation Matrix */}
            {selectedCommodities.length >= 2 && chartData.length > 0 && (
                <div className="card">
                    <h2 className="text-xl font-semibold text-ark-fg mb-4">Price Correlations</h2>
                    <p className="text-ark-fg-dim text-sm mb-4">
                        Pearson correlation of annual average prices over the selected window.
                        +1 = move together perfectly, −1 = move oppositely.
                    </p>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr>
                                    <th className="text-left p-2 text-ark-fg-dim"></th>
                                    {selectedCommodities.map(c => (
                                        <th key={c} className="p-2 text-ark-fg-dim capitalize">{c}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {selectedCommodities.map((c1, i) => (
                                    <tr key={c1}>
                                        <td className="p-2 text-ark-fg-dim capitalize font-medium">{c1}</td>
                                        {selectedCommodities.map((c2, j) => {
                                            const correlation = i === j ? 1 : calculateCorrelation(chartData, c1, c2)
                                            const bgColor = correlation > 0.7 ? 'bg-green-900/30' :
                                                correlation > 0.3 ? 'bg-green-900/10' :
                                                    correlation < -0.3 ? 'bg-red-900/10' :
                                                        correlation < -0.7 ? 'bg-red-900/30' : ''
                                            return (
                                                <td key={c2} className={`p-2 text-center ${bgColor}`}>
                                                    <span className={correlation > 0.5 ? 'text-green-400' : correlation < -0.5 ? 'text-red-400' : 'text-ark-fg-dim'}>
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
