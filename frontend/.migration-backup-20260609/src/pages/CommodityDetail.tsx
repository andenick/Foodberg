import { ArrowLeft, TrendingDown, TrendingUp } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../services/api'
import {
    Area,
    AreaChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis
} from 'recharts'

interface WASDERecord {
    commodity: string
    statistic_category: string
    value: string
    numeric_value: number | null
    unit: string
    location: string
    year: number
    reference_period: string
}

export default function CommodityDetail() {
    const { commodityId } = useParams<{ commodityId: string }>()
    const [data, setData] = useState<WASDERecord[]>([])
    const [loading, setLoading] = useState(true)
    const [selectedMetric, setSelectedMetric] = useState<string>('all')
    const [timeRange, setTimeRange] = useState<string>('all')
    const [availableMetrics, setAvailableMetrics] = useState<string[]>([])

    useEffect(() => {
        if (commodityId) {
            loadCommodityData()
        }
    }, [commodityId])

    const loadCommodityData = async () => {
        try {
            const response = await api.getWASDEData(commodityId!, 5000)
            const result = response.data
            const records = result.data || []
            setData(records)

            // Extract unique metrics
            const metrics = [...new Set(records.map((r: WASDERecord) => r.statistic_category))]
            setAvailableMetrics(metrics.filter(Boolean) as string[])

            if (metrics.length > 0 && !metrics.includes(selectedMetric)) {
                setSelectedMetric(metrics[0] as string)
            }
        } catch (error) {
            console.error('Failed to load commodity data:', error)
        } finally {
            setLoading(false)
        }
    }

    // Filter and prepare chart data
    const getChartData = () => {
        let filtered = data

        // Filter by metric
        if (selectedMetric !== 'all') {
            filtered = filtered.filter(r => r.statistic_category === selectedMetric)
        }

        // Filter by time range
        const currentYear = new Date().getFullYear()
        if (timeRange !== 'all') {
            const years = parseInt(timeRange)
            filtered = filtered.filter(r => r.year >= currentYear - years)
        }

        // Group by year and calculate averages
        const yearlyData = filtered.reduce((acc: any, record) => {
            const year = record.year
            if (!acc[year]) {
                acc[year] = { year, values: [], count: 0 }
            }
            if (record.numeric_value !== null) {
                acc[year].values.push(record.numeric_value)
                acc[year].count++
            }
            return acc
        }, {})

        return Object.values(yearlyData)
            .map((item: any) => ({
                year: item.year,
                value: item.values.length > 0
                    ? item.values.reduce((a: number, b: number) => a + b, 0) / item.values.length
                    : null,
                count: item.count
            }))
            .filter((item: any) => item.value !== null)
            .sort((a: any, b: any) => a.year - b.year)
    }

    const chartData = getChartData()

    // Calculate statistics
    const stats = {
        minValue: chartData.length > 0 ? Math.min(...chartData.map(d => d.value as number)) : 0,
        maxValue: chartData.length > 0 ? Math.max(...chartData.map(d => d.value as number)) : 0,
        avgValue: chartData.length > 0
            ? chartData.reduce((sum, d) => sum + (d.value as number), 0) / chartData.length
            : 0,
        yearRange: chartData.length > 0
            ? `${chartData[0].year} - ${chartData[chartData.length - 1].year}`
            : 'N/A',
        totalRecords: data.length
    }

    // Calculate year-over-year change
    const yoyChange = chartData.length >= 2
        ? ((chartData[chartData.length - 1].value as number) - (chartData[chartData.length - 2].value as number))
        / (chartData[chartData.length - 2].value as number) * 100
        : 0

    if (loading) {
        return (
            <div className="max-w-7xl mx-auto px-4 py-8 flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                    <div className="animate-spin w-12 h-12 border-2 border-emerald-400 border-t-transparent rounded-full mx-auto"></div>
                    <p className="text-slate-400 mt-4">Loading commodity data...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Breadcrumb */}
            <div className="mb-6">
                <Link to="/explore" className="flex items-center text-slate-400 hover:text-emerald-400 transition-colors">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Price Explorer
                </Link>
            </div>

            {/* Header */}
            <div className="mb-8">
                <h1 className="text-4xl font-bold text-slate-100 mb-2 capitalize">{commodityId}</h1>
                <p className="text-slate-400">
                    Historical price and production data from USDA WASDE reports
                </p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
                <div className="card bg-gradient-to-br from-emerald-900/20 to-emerald-800/10 border-emerald-700/30">
                    <div className="text-sm text-slate-400 mb-1">Latest Value</div>
                    <div className="text-2xl font-bold text-emerald-400">
                        {chartData.length > 0 ? (chartData[chartData.length - 1].value as number).toLocaleString(undefined, { maximumFractionDigits: 2 }) : 'N/A'}
                    </div>
                </div>
                <div className="card">
                    <div className="text-sm text-slate-400 mb-1">YoY Change</div>
                    <div className={`text-2xl font-bold flex items-center ${yoyChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {yoyChange >= 0 ? <TrendingUp className="w-5 h-5 mr-1" /> : <TrendingDown className="w-5 h-5 mr-1" />}
                        {yoyChange.toFixed(1)}%
                    </div>
                </div>
                <div className="card">
                    <div className="text-sm text-slate-400 mb-1">Average</div>
                    <div className="text-2xl font-bold text-slate-100">
                        {stats.avgValue.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                    </div>
                </div>
                <div className="card">
                    <div className="text-sm text-slate-400 mb-1">Data Range</div>
                    <div className="text-lg font-bold text-slate-100">{stats.yearRange}</div>
                </div>
                <div className="card">
                    <div className="text-sm text-slate-400 mb-1">Total Records</div>
                    <div className="text-2xl font-bold text-slate-100">{stats.totalRecords.toLocaleString()}</div>
                </div>
            </div>

            {/* Filters */}
            <div className="card mb-6">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1">
                        <label className="block text-sm text-slate-400 mb-2">Metric</label>
                        <select
                            value={selectedMetric}
                            onChange={(e) => setSelectedMetric(e.target.value)}
                            className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:border-emerald-500"
                        >
                            <option value="all">All Metrics (Averaged)</option>
                            {availableMetrics.slice(0, 20).map(metric => (
                                <option key={metric} value={metric}>{metric}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm text-slate-400 mb-2">Time Range</label>
                        <div className="flex gap-2">
                            {[
                                { value: '5', label: '5Y' },
                                { value: '10', label: '10Y' },
                                { value: '20', label: '20Y' },
                                { value: 'all', label: 'All' }
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
                </div>
            </div>

            {/* Main Chart */}
            <div className="card mb-8">
                <h2 className="text-xl font-semibold text-slate-100 mb-4">Price History</h2>
                <div className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData}>
                            <defs>
                                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                                </linearGradient>
                            </defs>
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
                                formatter={(value: number) => [value.toLocaleString(undefined, { maximumFractionDigits: 2 }), 'Value']}
                            />
                            <Area
                                type="monotone"
                                dataKey="value"
                                stroke="#10B981"
                                strokeWidth={2}
                                fill="url(#colorValue)"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Related Commodities */}
            <div className="card">
                <h2 className="text-xl font-semibold text-slate-100 mb-4">Compare with Related Commodities</h2>
                <div className="flex flex-wrap gap-2">
                    {['wheat', 'corn', 'soybeans', 'rice', 'cotton', 'cattle'].filter(c => c !== commodityId).map(commodity => (
                        <Link
                            key={commodity}
                            to={`/commodity/${commodity}`}
                            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg capitalize transition-colors"
                        >
                            {commodity}
                        </Link>
                    ))}
                </div>
                <p className="text-sm text-slate-500 mt-4">
                    For multi-commodity comparison charts, visit the <Link to="/trends" className="text-emerald-400 hover:underline">Historical Trends</Link> page.
                </p>
            </div>
        </div>
    )
}
