import { BarChart3, Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
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
    'Other': ['hay', 'tobacco', 'honey', 'potatoes', 'coffee', 'sugar']
}

interface CommodityData {
    commodity: string
    filename: string
    last_updated: string
    file_size_mb: number
}

interface SourceCov {
    points: number
    frequency: string
    start: string
    end: string
    label?: string
    n_years?: number
    unit?: string
}

type Coverage = Partial<Record<'av' | 'nass' | 'pinksheet' | 'retail', SourceCov>>

interface SeriesRow { date: string; year: number; price: number }

interface SourcePayload {
    commodity: string
    source: string
    has_history: boolean
    label?: string
    unit?: string | null
    data_points: number
    date_range?: { start: string; end: string }
    data: SeriesRow[]
    note?: string
}

const SOURCE_LABELS: Record<string, string> = {
    nass: 'US farm gate (USDA)',
    av: 'Global spot (monthly)',
    pinksheet: 'Global spot (Pink Sheet)',
    retail: 'US retail (BLS)',
}

// Preferred display order for source tabs.
const SOURCE_ORDER: Array<'nass' | 'av' | 'pinksheet' | 'retail'> = ['nass', 'av', 'pinksheet', 'retail']

export default function PriceExplorer() {
    const [commodities, setCommodities] = useState<CommodityData[]>([])
    const [coverage, setCoverage] = useState<Record<string, Coverage>>({})
    const [selectedCategory, setSelectedCategory] = useState<string>('all')
    const [searchTerm, setSearchTerm] = useState('')
    const [loading, setLoading] = useState(true)
    const [series, setSeries] = useState<SourcePayload | null>(null)
    const [selectedCommodity, setSelectedCommodity] = useState<string | null>(null)
    const [selectedSource, setSelectedSource] = useState<string>('nass')
    const [fallbackValue, setFallbackValue] = useState<{ price: number; year: number; unit: string } | null>(null)
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

    const covFor = (name: string): Coverage => coverage[name.toLowerCase()] ?? {}
    const sourcesFor = (name: string) =>
        SOURCE_ORDER.filter((s) => covFor(name)[s] && (covFor(name)[s] as SourceCov).points > 1)

    const loadSeries = async (commodity: string, source: string) => {
        setSelectedCommodity(commodity)
        setSelectedSource(source)
        setSeries(null)
        setFallbackValue(null)
        const slug = commodity.toLowerCase()
        try {
            if (source === 'av') {
                const res = await api.getPriceHistory(slug)
                const p = res.data
                setSeries({
                    commodity: slug, source: 'av', has_history: p.has_history,
                    label: p.source || 'Alpha Vantage global spot',
                    unit: p.unit, data_points: p.data_points,
                    date_range: p.date_range,
                    data: (p.data || []).map((r: { date: string; year: number; price: number }) => ({
                        date: String(r.date).slice(0, 10), year: r.year, price: r.price,
                    })),
                })
            } else if (source === 'none') {
                // No real series anywhere: show the latest WASDE value honestly.
                const res = await api.getWASDEData(slug, 200)
                const rows = (res.data.data || []).filter((r: { numeric_value: number | null }) => r.numeric_value !== null)
                if (rows.length) {
                    const latest = rows[0]
                    setFallbackValue({ price: latest.numeric_value, year: latest.year, unit: latest.unit || '' })
                }
                setSeries({
                    commodity: slug, source: 'none', has_history: false,
                    data_points: rows.length, data: [],
                    note: 'No multi-point price series in any local source for this commodity.',
                })
            } else {
                const res = await api.getSourceHistory(slug, source)
                setSeries(res.data)
            }
        } catch (error) {
            console.error('Failed to load series:', error)
        }
    }

    const selectCommodity = (commodity: string) => {
        const avail = sourcesFor(commodity)
        loadSeries(commodity, avail.length ? avail[0] : 'none')
    }

    // Coverage-aware sort: most-covered commodities first.
    const filteredCommodities = useMemo(() => commodities
        .filter(c => {
            const matchesSearch = c.commodity.toLowerCase().includes(searchTerm.toLowerCase())
            if (selectedCategory === 'all') return matchesSearch
            const categoryItems = COMMODITY_CATEGORIES[selectedCategory as keyof typeof COMMODITY_CATEGORIES] || []
            return matchesSearch && categoryItems.includes(c.commodity.toLowerCase())
        })
        .sort((a, b) => {
            const an = sourcesFor(a.commodity).length
            const bn = sourcesFor(b.commodity).length
            return an !== bn ? bn - an : a.commodity.localeCompare(b.commodity)
        }), [commodities, searchTerm, selectedCategory, coverage])

    const spanLabel = (name: string): string | null => {
        const cov = covFor(name)
        const best = SOURCE_ORDER.map(s => cov[s]).find(Boolean)
        if (!best) return null
        const y0 = best.start?.slice(0, 4)
        const y1 = best.end?.slice(0, 4)
        return y0 && y1 ? `${y0}–${y1}` : null
    }

    const unitLabel = series?.unit || 'Value'
    const chartData = series?.data ?? []
    const latestRow = chartData.length ? chartData[chartData.length - 1] : null
    const availableSources = selectedCommodity ? sourcesFor(selectedCommodity) : []

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-ark-fg mb-2">Price Explorer</h1>
                <p className="text-ark-fg-dim">
                    Real price history from four baked sources — USDA farm-gate prices (annual,
                    many series back to 1908), global spot prices (Alpha Vantage and the World Bank
                    Pink Sheet, monthly), and US retail averages (BLS, monthly). Coverage badges are
                    computed from the data itself; nothing is interpolated or extrapolated.
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
                                    const nSrc = sourcesFor(commodity.commodity).length
                                    const span = spanLabel(commodity.commodity)
                                    return (
                                        <button
                                            key={commodity.commodity}
                                            onClick={() => selectCommodity(commodity.commodity)}
                                            className={`w-full text-left p-3 rounded-lg transition-colors ${selectedCommodity === commodity.commodity
                                                    ? 'bg-emerald-600/20 border border-emerald-500/50'
                                                    : nSrc
                                                        ? 'bg-ark-bg-soft hover:bg-ark-tag border border-transparent'
                                                        : 'bg-ark-bg-soft hover:bg-ark-tag border border-transparent opacity-70'
                                                }`}
                                        >
                                            <div className="flex justify-between items-center">
                                                <span className="font-medium text-ark-fg capitalize">
                                                    {commodity.commodity}
                                                </span>
                                                {nSrc ? (
                                                    <span className="text-[10px] font-semibold uppercase tracking-wide text-emerald-400 bg-emerald-900/30 px-1.5 py-0.5 rounded">
                                                        {nSrc} source{nSrc > 1 ? 's' : ''}
                                                    </span>
                                                ) : (
                                                    <span className="text-[10px] font-semibold uppercase tracking-wide text-amber-400/80 bg-amber-900/20 px-1.5 py-0.5 rounded">
                                                        1 yr only
                                                    </span>
                                                )}
                                            </div>
                                            <div className="text-xs text-ark-fg-dim mt-1">
                                                {span ? `History ${span}` : 'Single WASDE marketing year'}
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
                                <div className="flex justify-between items-center mb-2 flex-wrap gap-2">
                                    <h2 className="text-xl font-semibold text-ark-fg capitalize">
                                        {selectedCommodity} Price History
                                    </h2>
                                    <Link
                                        to={`/commodity/${selectedCommodity}`}
                                        className="text-sm text-emerald-400 hover:text-emerald-300"
                                    >
                                        View Details →
                                    </Link>
                                </div>

                                {/* Source tabs */}
                                {availableSources.length > 0 && (
                                    <div className="flex gap-2 mb-4 flex-wrap">
                                        {availableSources.map((s) => (
                                            <button
                                                key={s}
                                                onClick={() => loadSeries(selectedCommodity, s)}
                                                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${selectedSource === s
                                                        ? 'bg-emerald-600 text-white'
                                                        : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                                    }`}
                                            >
                                                {SOURCE_LABELS[s]}
                                            </button>
                                        ))}
                                    </div>
                                )}

                                {series.has_history && chartData.length > 1 ? (
                                    <div className="h-[380px]">
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
                                                    formatter={(value: number) => [value.toLocaleString(undefined, { maximumFractionDigits: 3 }), unitLabel]}
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
                                    <div className="h-[380px] flex flex-col items-center justify-center text-center">
                                        <div className="text-sm uppercase tracking-wide text-amber-400/80 mb-2">
                                            No time series in the local dataset
                                        </div>
                                        {fallbackValue ? (
                                            <>
                                                <div className="text-5xl font-bold text-ark-fg">
                                                    {fallbackValue.price.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                                                </div>
                                                <div className="text-ark-fg-dim mt-2">
                                                    {fallbackValue.unit} · marketing year {fallbackValue.year} (USDA WASDE)
                                                </div>
                                            </>
                                        ) : (
                                            <div className="text-ark-fg-dim">Loading…</div>
                                        )}
                                        <p className="text-xs text-ark-fg-dim mt-4 max-w-md">
                                            {series.note || 'No multi-point series available for this commodity.'}
                                        </p>
                                    </div>
                                )}

                                <ChartMetaStrip
                                    meta={{
                                        source: series.label || (series.source === 'none' ? 'USDA NASS WASDE (latest value)' : series.source),
                                        unit: unitLabel,
                                        dateRange: series.date_range
                                            ? `${series.date_range.start} → ${series.date_range.end}`
                                            : null,
                                        points: series.data_points,
                                        latestLabel: 'Latest',
                                        latestValue: latestRow
                                            ? `${latestRow.price.toLocaleString(undefined, { maximumFractionDigits: 3 })} (${latestRow.date})`
                                            : null,
                                    }}
                                />

                                <ScrollableDataTable
                                    rows={chartData.map(r => ({ date: r.date, value: r.price }))}
                                    columns={[
                                        { key: 'date', label: series.source === 'nass' ? 'Year' : 'Month' },
                                        { key: 'value', label: unitLabel, numeric: true },
                                    ]}
                                    filename={`foodberg_${selectedCommodity}_${selectedSource}_prices`}
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
                                <p className="text-sm mt-2">Badges show how many real price sources each commodity has</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
