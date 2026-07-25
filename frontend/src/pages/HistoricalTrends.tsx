import { History } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
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
import { downloadCsv, useArkTheme } from '../arcanum/arkChartTheme'
import { ChartMetaStrip, ScrollableDataTable } from '../components/ChartDetails'
import { ReindexControl, distinctYears, reindexRows } from '../components/ReindexControl'

// Color palette for multiple commodities
const COLORS = [
    '#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
]

interface SourceCov { points: number; start: string; end: string }
type Coverage = Partial<Record<'av' | 'nass' | 'pinksheet' | 'retail', SourceCov>>

/* Preferred series per commodity for trend comparison: USDA farm-gate annual
   first (longest spans, most commodities), then Alpha Vantage monthly, then
   Pink Sheet monthly, then BLS US retail monthly. Monthly series are averaged
   into annual points so all lines share the x-axis.

   'retail' was omitted from this list, which meant BLS Average Price series
   could never appear on Trends at all — including every retail-only item
   (tomatoes, lettuce, bacon, flour, cheese …). It is last in preference so a
   commodity that also has a farm-gate or spot series keeps its longer history,
   but retail-only items are now eligible instead of invisible. */
type TrendSource = 'nass' | 'av' | 'pinksheet' | 'retail'
const PREFERENCE: TrendSource[] = ['nass', 'av', 'pinksheet', 'retail']

export default function HistoricalTrends() {
    const [coverage, setCoverage] = useState<Record<string, Coverage>>({})
    const [eligible, setEligible] = useState<string[]>([])
    const [displayNames, setDisplayNames] = useState<Record<string, string>>({})
    const [itemFilter, setItemFilter] = useState('')
    const [selectedCommodities, setSelectedCommodities] = useState<string[]>(['wheat', 'corn'])
    const [chartData, setChartData] = useState<Record<string, number>[]>([])
    const [units, setUnits] = useState<Record<string, string>>({})
    const [sourcesUsed, setSourcesUsed] = useState<Record<string, string>>({})
    const [loading, setLoading] = useState(true)
    const [timeRange, setTimeRange] = useState<string>('all')
    const [baseYear, setBaseYear] = useState<number | null>(null)
    const t = useArkTheme()

    // Base-year options + client-side reindexed view of exactly what's plotted.
    const baseYears = useMemo(() => distinctYears(chartData, 'year'), [chartData])
    const displayData = useMemo(
        () => reindexRows(chartData, selectedCommodities, baseYear, 'year'),
        [chartData, selectedCommodities, baseYear],
    )

    // Drop a base year that no longer exists in the visible window.
    useEffect(() => {
        if (baseYear !== null && !baseYears.includes(baseYear)) setBaseYear(null)
    }, [baseYears, baseYear])

    useEffect(() => {
        api.getPriceCoverage()
            .then((res) => {
                const cov: Record<string, Coverage> = res.data.commodities || {}
                setCoverage(cov)
                setDisplayNames(res.data.display_names || {})
                setEligible(Object.keys(cov)
                    .filter(slug => PREFERENCE.some(s => cov[slug][s] && (cov[slug][s] as SourceCov).points > 1))
                    .sort())
            })
            .catch((e) => console.error('Failed to load coverage:', e))
    }, [])

    useEffect(() => {
        loadMultiCommodityData()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedCommodities, timeRange, coverage])

    const preferredSource = (slug: string): TrendSource | null => {
        const cov = coverage[slug]
        if (!cov) return null
        return PREFERENCE.find(s => cov[s] && (cov[s] as SourceCov).points > 1) ?? null
    }

    const loadMultiCommodityData = async () => {
        if (selectedCommodities.length === 0 || !Object.keys(coverage).length) {
            setChartData([])
            return
        }
        setLoading(true)
        try {
            const results = await Promise.all(
                selectedCommodities.map(async (commodity) => {
                    const src = preferredSource(commodity)
                    if (!src) return { commodity, src: null, rows: [], unit: '' }
                    if (src === 'av') {
                        const res = await api.getPriceHistory(commodity)
                        return {
                            commodity, src,
                            rows: (res.data.data || []).map((r: { year: number; price: number }) => ({ year: r.year, value: r.price })),
                            unit: res.data.unit || 'USD',
                        }
                    }
                    const res = await api.getSourceHistory(commodity, src)
                    return {
                        commodity, src,
                        rows: (res.data.data || []).map((r: { year: number; price: number }) => ({ year: r.year, value: r.price })),
                        unit: res.data.unit || 'USD',
                    }
                })
            )

            const nextUnits: Record<string, string> = {}
            const nextSources: Record<string, string> = {}
            const yearlyData: Record<number, Record<string, number>> = {}

            results.forEach(({ commodity, src, rows, unit }) => {
                if (!src || !rows.length) return
                nextUnits[commodity] = unit
                nextSources[commodity] = src
                const byYear: Record<number, number[]> = {}
                for (const row of rows) {
                    if (row.value !== null && row.value !== undefined) {
                        (byYear[row.year] ||= []).push(row.value)
                    }
                }
                Object.entries(byYear).forEach(([year, values]) => {
                    const y = Number(year)
                    yearlyData[y] ||= { year: y }
                    yearlyData[y][commodity] = values.reduce((a, b) => a + b, 0) / values.length
                })
            })

            let chartArray = Object.values(yearlyData).sort((a, b) => a.year - b.year)
            if (timeRange !== 'all') {
                const years = parseInt(timeRange)
                const currentYear = new Date().getFullYear()
                chartArray = chartArray.filter((d) => d.year >= currentYear - years)
            }

            setUnits(nextUnits)
            setSourcesUsed(nextSources)
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
    const calculateCorrelation = (data: Record<string, number>[], key1: string, key2: string): number => {
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

    const SRC_SHORT: Record<string, string> = { nass: 'USDA farm gate', av: 'global spot', pinksheet: 'Pink Sheet' }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-ark-fg mb-2 flex items-center">
                    <History className="w-8 h-8 mr-3 text-purple-400" />
                    Historical Trends
                </h1>
                <p className="text-ark-fg-dim">
                    Compare long-term price trends — every commodity with a genuine multi-year
                    series qualifies (USDA farm-gate annual prices back to 1908 for the majors,
                    global spot prices where available). Monthly series are shown as annual
                    averages so all lines share one axis. Units differ per commodity — compare
                    shapes, not levels.
                </p>
            </div>

            {/* Commodity Selector */}
            <div className="card mb-6">
                <h2 className="text-lg font-semibold text-ark-fg mb-4">
                    Select Commodities to Compare (max 6)
                    <span className="text-sm text-ark-fg-dim ml-2">
                        ({selectedCommodities.length} selected · {eligible.length} have real history)
                    </span>
                </h2>
                <input
                    type="text"
                    value={itemFilter}
                    onChange={(e) => setItemFilter(e.target.value)}
                    placeholder="Filter items — try “tomato”, “beef”, “wheat”…"
                    className="w-full mb-3 px-3 py-2 bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg placeholder-ark-fg-dim focus:outline-none focus:border-emerald-500"
                />
                <div className="flex flex-wrap gap-2 max-h-56 overflow-y-auto">
                    {eligible
                        .filter((slug) => {
                            const needle = itemFilter.trim().toLowerCase()
                            if (!needle) return true
                            return slug.includes(needle)
                                || (displayNames[slug] ?? '').toLowerCase().includes(needle)
                        })
                        .map((slug) => (
                        <button
                            key={slug}
                            onClick={() => toggleCommodity(slug)}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${displayNames[slug] ? '' : 'capitalize '}${selectedCommodities.includes(slug)
                                ? 'text-white'
                                : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                }`}
                            style={selectedCommodities.includes(slug) ? {
                                backgroundColor: COLORS[selectedCommodities.indexOf(slug) % COLORS.length]
                            } : {}}
                            disabled={!selectedCommodities.includes(slug) && selectedCommodities.length >= 6}
                        >
                            {displayNames[slug] ?? slug}
                        </button>
                    ))}
                </div>
            </div>

            {/* Time range */}
            <div className="card mb-6">
                <label className="block text-sm text-ark-fg-dim mb-2">Time Range</label>
                <div className="flex gap-2 flex-wrap">
                    {[
                        { value: '10', label: '10 Years' },
                        { value: '20', label: '20 Years' },
                        { value: '50', label: '50 Years' },
                        { value: '100', label: '100 Years' },
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
                <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
                    <h2 className="text-xl font-semibold text-ark-fg">Historical Price Comparison</h2>
                    <div className="flex items-center gap-3 flex-wrap">
                        <ReindexControl
                            id="trends-reindex"
                            years={baseYears}
                            baseYear={baseYear}
                            onChange={setBaseYear}
                        />
                        <button
                            type="button"
                            className="ark-btn ark-btn-sm ark-btn-ghost"
                            onClick={() => downloadCsv(displayData, 'foodberg_trends')}
                            disabled={displayData.length === 0}
                        >
                            Download CSV
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="h-[500px] flex items-center justify-center">
                        <div className="text-center">
                            <div className="animate-spin w-12 h-12 border-2 border-emerald-400 border-t-transparent rounded-full mx-auto"></div>
                            <p className="text-ark-fg-dim mt-4">Loading price data...</p>
                        </div>
                    </div>
                ) : displayData.length > 0 ? (
                    <>
                        <div className="h-[500px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={displayData} margin={{ left: 12, bottom: 8 }}>
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
                                        label={{
                                            value: baseYear
                                                ? `Index (${baseYear} = 100)`
                                                : 'Price (annual average; per-unit basis varies)',
                                            angle: -90, position: 'insideLeft', fill: t.dim, fontSize: 11
                                        }}
                                    />
                                    <Tooltip
                                        contentStyle={t.tooltip}
                                        labelStyle={{ color: t.fg }}
                                        formatter={(value: number, name: string) => [
                                            baseYear
                                                ? `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })} (${baseYear}=100)`
                                                : `${value.toLocaleString(undefined, { maximumFractionDigits: 3 })} ${units[name] || ''}`,
                                            `${name.charAt(0).toUpperCase() + name.slice(1)} (${SRC_SHORT[sourcesUsed[name]] || ''})`
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
                                source: selectedCommodities
                                    .filter(c => sourcesUsed[c])
                                    .map(c => `${c}: ${SRC_SHORT[sourcesUsed[c]]}`).join(' · '),
                                unit: baseYear
                                    ? `Reindexed (${baseYear} = 100, computed in-browser)`
                                    : selectedCommodities.map(c => `${c}: ${units[c] || '—'}`).join(' · '),
                                dateRange: yearSpan,
                                points: displayData.length,
                                note: baseYear
                                    ? `Each series rescaled to 100 at ${baseYear}, so shapes are directly comparable across commodities and units.`
                                    : 'Each point is the annual average of that commodity\'s preferred real series. Units differ — compare shapes, not levels.',
                            }}
                        />

                        <ScrollableDataTable
                            rows={displayData}
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
            {selectedCommodities.length >= 2 && displayData.length > 0 && (
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
                                            const correlation = i === j ? 1 : calculateCorrelation(displayData, c1, c2)
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
