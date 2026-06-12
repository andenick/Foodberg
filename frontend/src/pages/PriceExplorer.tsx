import { BarChart3, Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
    CartesianGrid,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis
} from 'recharts'
import { api } from '../services/api'
import { useArkTheme } from '../arcanum/arkChartTheme'
import { ChartMetaStrip, ScrollableDataTable } from '../components/ChartDetails'

// Commodity categories for filtering
const COMMODITY_CATEGORIES = {
    'Grains': ['wheat', 'corn', 'rice', 'barley', 'oats', 'sorghum', 'rye'],
    'Oilseeds': ['soybeans', 'canola', 'sunflower', 'peanuts', 'flaxseed'],
    'Livestock': ['cattle', 'hogs', 'sheep', 'goats', 'chickens', 'turkeys'],
    'Dairy & Eggs': ['milk', 'eggs'],
    'Fiber': ['cotton'],
    'Fruits': ['apples', 'grapes', 'blueberries', 'strawberries', 'cranberries'],
    'Other': ['hay', 'tobacco', 'honey', 'potatoes']
}

interface CommodityData {
    commodity: string
    filename: string
    last_updated: string
    file_size_mb: number
}

interface Coverage {
    has_history: boolean
    points: number
    start: string
    end: string
    source: string
}

interface SeriesPayload {
    commodity: string
    has_history: boolean
    source: string | null
    unit?: string | null
    currency?: string | null
    data_points: number
    date_range?: { start: string; end: string }
    data: Array<{ year: number; numeric_value: number | null; date?: string; unit?: string; statistic_category?: string; location?: string }>
    note?: string
}

export default function PriceExplorer() {
    const [commodities, setCommodities] = useState<CommodityData[]>([])
    const [coverage, setCoverage] = useState<Record<string, Coverage>>({})
    const [selectedCategory, setSelectedCategory] = useState<string>('all')
    const [searchTerm, setSearchTerm] = useState('')
    const [loading, setLoading] = useState(true)
    const [series, setSeries] = useState<SeriesPayload | null>(null)
    const [chartData, setChartData] = useState<Array<{ year: number; price: number }>>([])
    const [selectedCommodity, setSelectedCommodity] = useState<string | null>(null)
    const t = useArkTheme()

    useEffect(() => {
        Promise.all([api.getWASDECommodities(), api.getPriceCoverage()])
            .then(([cRes, covRes]) => {
                setCommodities(cRes.data.commodities || [])
                setCoverage(covRes.data.commodities || {})
            })
            .catch((error) => console.error('Failed to load commodities:', error))
            .finally(() => setLoading(false))
    }, [])

    const loadCommodityPrices = async (commodity: string) => {
        setSelectedCommodity(commodity)
        setSeries(null)
        setChartData([])
        try {
            const response = await api.getWASDEData(commodity, 5000)
            const payload: SeriesPayload = response.data
            setSeries(payload)

            // Yearly averages for the chart (the real monthly series averages
            // cleanly; the WASDE fallback collapses to its single marketing year).
            const yearly: Record<number, number[]> = {}
            for (const rec of payload.data || []) {
                if (rec.numeric_value !== null && rec.numeric_value !== undefined) {
                    (yearly[rec.year] ||= []).push(rec.numeric_value)
                }
            }
            setChartData(
                Object.entries(yearly)
                    .map(([year, vals]) => ({
                        year: Number(year),
                        price: vals.reduce((a, b) => a + b, 0) / vals.length,
                    }))
                    .sort((a, b) => a.year - b.year)
            )
        } catch (error) {
            console.error('Failed to load prices:', error)
        }
    }

    const hasHistory = (name: string) => Boolean(coverage[name.toLowerCase()]?.has_history)

    // Full-history commodities first, then the single-marketing-year ones.
    const filteredCommodities = commodities
        .filter(c => {
            const matchesSearch = c.commodity.toLowerCase().includes(searchTerm.toLowerCase())
            if (selectedCategory === 'all') return matchesSearch
            const categoryItems = COMMODITY_CATEGORIES[selectedCategory as keyof typeof COMMODITY_CATEGORIES] || []
            return matchesSearch && categoryItems.includes(c.commodity.toLowerCase())
        })
        .sort((a, b) => {
            const ah = hasHistory(a.commodity) ? 0 : 1
            const bh = hasHistory(b.commodity) ? 0 : 1
            return ah !== bh ? ah - bh : a.commodity.localeCompare(b.commodity)
        })

    const unitLabel = series?.unit || series?.data?.[0]?.unit || 'Value'
    const isHistory = Boolean(series?.has_history)
    const latestRow = chartData.length ? chartData[chartData.length - 1] : null

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-ark-fg mb-2">Price Explorer</h1>
                <p className="text-ark-fg-dim">
                    Browse historical food commodity prices. Genuine monthly history (1992–present)
                    exists for wheat, corn, coffee, sugar, and cotton; other commodities carry a
                    single USDA WASDE marketing year — shown honestly, never extrapolated.
                </p>
            </div>

            {/* Search and Filters */}
            <div className="card mb-6">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-ark-fg-dim" />
                            <input
                                type="text"
                                placeholder="Search commodities..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 bg-ark-tag border border-ark-line rounded-lg text-ark-fg placeholder-ark-fg-dim focus:outline-none focus:border-emerald-500"
                            />
                        </div>
                    </div>
                    <div className="flex gap-2 flex-wrap">
                        <button
                            onClick={() => setSelectedCategory('all')}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${selectedCategory === 'all'
                                    ? 'bg-emerald-600 text-white'
                                    : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                }`}
                        >
                            All
                        </button>
                        {Object.keys(COMMODITY_CATEGORIES).map(category => (
                            <button
                                key={category}
                                onClick={() => setSelectedCategory(category)}
                                className={`px-4 py-2 rounded-lg font-medium transition-colors ${selectedCategory === category
                                        ? 'bg-emerald-600 text-white'
                                        : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                    }`}
                            >
                                {category}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Commodity List */}
                <div className="lg:col-span-1">
                    <div className="card">
                        <h2 className="text-lg font-semibold text-ark-fg mb-4 flex items-center">
                            <BarChart3 className="w-5 h-5 mr-2 text-emerald-400" />
                            Commodities ({filteredCommodities.length})
                        </h2>

                        {loading ? (
                            <div className="text-center py-8">
                                <div className="animate-spin w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full mx-auto"></div>
                                <p className="text-ark-fg-dim mt-2">Loading commodities...</p>
                            </div>
                        ) : (
                            <div className="space-y-2 max-h-[600px] overflow-y-auto">
                                {filteredCommodities.map(commodity => {
                                    const cov = coverage[commodity.commodity.toLowerCase()]
                                    return (
                                        <button
                                            key={commodity.commodity}
                                            onClick={() => loadCommodityPrices(commodity.commodity)}
                                            className={`w-full text-left p-3 rounded-lg transition-colors ${selectedCommodity === commodity.commodity
                                                    ? 'bg-emerald-600/20 border border-emerald-500/50'
                                                    : cov
                                                        ? 'bg-ark-bg-soft hover:bg-ark-tag border border-transparent'
                                                        : 'bg-ark-bg-soft hover:bg-ark-tag border border-transparent opacity-70'
                                                }`}
                                        >
                                            <div className="flex justify-between items-center">
                                                <span className="font-medium text-ark-fg capitalize">
                                                    {commodity.commodity}
                                                </span>
                                                {cov ? (
                                                    <span className="text-[10px] font-semibold uppercase tracking-wide text-emerald-400 bg-emerald-900/30 px-1.5 py-0.5 rounded">
                                                        {cov.points} obs
                                                    </span>
                                                ) : (
                                                    <span className="text-[10px] font-semibold uppercase tracking-wide text-amber-400/80 bg-amber-900/20 px-1.5 py-0.5 rounded">
                                                        1 yr only
                                                    </span>
                                                )}
                                            </div>
                                            <div className="text-xs text-ark-fg-dim mt-1">
                                                {cov
                                                    ? `Monthly, ${cov.start.slice(0, 4)}–${cov.end.slice(0, 4)}`
                                                    : 'Single WASDE marketing year'}
                                            </div>
                                        </button>
                                    )
                                })}
                            </div>
                        )}
                    </div>
                </div>

                {/* Price Chart */}
                <div className="lg:col-span-2">
                    <div className="card h-full">
                        {selectedCommodity && series ? (
                            <>
                                <div className="flex justify-between items-center mb-4">
                                    <h2 className="text-xl font-semibold text-ark-fg capitalize">
                                        {selectedCommodity} {isHistory ? 'Price History' : '— Latest Marketing Year'}
                                    </h2>
                                    <Link
                                        to={`/commodity/${selectedCommodity}`}
                                        className="text-sm text-emerald-400 hover:text-emerald-300"
                                    >
                                        View Details →
                                    </Link>
                                </div>

                                {isHistory && chartData.length > 1 ? (
                                    <div className="h-[400px]">
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
                                                    label={{ value: unitLabel, angle: -90, position: 'insideLeft', fill: t.dim, fontSize: 12 }}
                                                />
                                                <Tooltip
                                                    contentStyle={t.tooltip}
                                                    labelStyle={{ color: t.fg }}
                                                    formatter={(value: number) => [value.toLocaleString(undefined, { maximumFractionDigits: 2 }), unitLabel]}
                                                    labelFormatter={(label) => `Year ${label} (annual average)`}
                                                />
                                                <Line
                                                    type="monotone"
                                                    dataKey="price"
                                                    stroke={t.accent}
                                                    strokeWidth={2}
                                                    dot={false}
                                                    activeDot={{ r: 6, fill: t.accent }}
                                                />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                ) : (
                                    /* Honest single-point view: a stat card, not a fake line. */
                                    <div className="h-[400px] flex flex-col items-center justify-center text-center">
                                        <div className="text-sm uppercase tracking-wide text-amber-400/80 mb-2">
                                            No time series in the local dataset
                                        </div>
                                        {latestRow ? (
                                            <>
                                                <div className="text-5xl font-bold text-ark-fg">
                                                    {latestRow.price.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                                                </div>
                                                <div className="text-ark-fg-dim mt-2">
                                                    {unitLabel} · marketing year {latestRow.year} (USDA WASDE)
                                                </div>
                                            </>
                                        ) : (
                                            <div className="text-ark-fg-dim">No price observations available.</div>
                                        )}
                                        <p className="text-xs text-ark-fg-dim mt-4 max-w-md">
                                            {series.note ||
                                                'The local dataset holds a single USDA WASDE marketing year for this commodity. Real monthly history exists for wheat, corn, coffee, sugar, and cotton.'}
                                        </p>
                                    </div>
                                )}

                                <ChartMetaStrip
                                    meta={{
                                        source: series.source || 'USDA NASS WASDE (via Robin)',
                                        unit: unitLabel,
                                        dateRange: series.date_range
                                            ? `${series.date_range.start.slice(0, 10)} → ${series.date_range.end.slice(0, 10)}`
                                            : (latestRow ? `marketing year ${latestRow.year}` : null),
                                        points: series.data_points,
                                        latestLabel: 'Latest (annual avg)',
                                        latestValue: latestRow
                                            ? `${latestRow.price.toLocaleString(undefined, { maximumFractionDigits: 2 })} (${latestRow.year})`
                                            : null,
                                    }}
                                />

                                <ScrollableDataTable
                                    rows={isHistory
                                        ? (series.data || []).map(r => ({ date: r.date?.slice(0, 10), value: r.numeric_value }))
                                        : chartData.map(r => ({ year: r.year, value: r.price }))}
                                    columns={isHistory
                                        ? [{ key: 'date', label: 'Month' }, { key: 'value', label: unitLabel, numeric: true }]
                                        : [{ key: 'year', label: 'Marketing year' }, { key: 'value', label: unitLabel, numeric: true }]}
                                    filename={`foodberg_${selectedCommodity}_prices`}
                                />
                            </>
                        ) : selectedCommodity ? (
                            <div className="h-[400px] flex items-center justify-center text-ark-fg-dim">
                                Loading price data...
                            </div>
                        ) : (
                            <div className="h-[400px] flex flex-col items-center justify-center text-ark-fg-dim">
                                <BarChart3 className="w-16 h-16 mb-4 text-ark-fg-dim" />
                                <p className="text-lg">Select a commodity to view price history</p>
                                <p className="text-sm mt-2">Commodities with a green badge have a real monthly series</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
