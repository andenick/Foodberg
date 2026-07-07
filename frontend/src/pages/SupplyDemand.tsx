import { Wheat } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../services/api'
import {
    CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { downloadCsv, useArkTheme } from '../arcanum/arkChartTheme'
import { ChartMetaStrip, ScrollableDataTable } from '../components/ChartDetails'
import { ReindexControl, reindexRows, distinctYears } from '../components/ReindexControl'

/* WASDE Supply & Demand — multi-year (marketing-year 1960→present) balance-sheet
   series from USDA FAS PS&D. Every commodity here is a genuine multi-decade time
   series (no single-year-only series). Gaps are real reporting gaps, never
   interpolated. World = sum of reported countries for additive attributes only. */

const COLORS = [
    '#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#06B6D4', '#84CC16',
]

type Region = 'United States' | 'World'

interface CommodityRow {
    commodity: string
    countries: number
    min_year: number
    max_year: number
    rows: number
}

interface AttrRow {
    attribute: string
    unit: string
    min_year: number
    max_year: number
    n_years: number
    is_aggregate: number
}

interface SeriesPayload {
    commodity: string
    region: string
    attribute: string
    unit: string
    is_aggregate: boolean
    note: string | null
    source: string
    source_url: string
    n_years: number
    year_range: { start: number; end: number }
    data: Array<{ year: number; value: number; unit: string }>
}

// Headline balance-sheet line items most users want, in display order.
const PREFERRED_ATTRS = [
    'Production', 'Domestic Consumption', 'Ending Stocks', 'Beginning Stocks',
    'Exports', 'Imports', 'Total Supply', 'Area Harvested', 'Yield',
]

export default function SupplyDemand() {
    const [commodities, setCommodities] = useState<CommodityRow[]>([])
    const [commodity, setCommodity] = useState<string>('Wheat')
    const [region, setRegion] = useState<Region>('World')
    const [attrs, setAttrs] = useState<AttrRow[]>([])
    const [selectedAttrs, setSelectedAttrs] = useState<string[]>(['Production', 'Ending Stocks'])
    const [seriesMap, setSeriesMap] = useState<Record<string, SeriesPayload>>({})
    const [baseYear, setBaseYear] = useState<number | null>(null)
    const [loading, setLoading] = useState(true)
    const t = useArkTheme()

    // Load commodity list once.
    useEffect(() => {
        api.getPsdCommodities()
            .then(res => {
                const rows = (res.data.commodities || []) as CommodityRow[]
                setCommodities(rows)
                if (rows.length && !rows.find(r => r.commodity === commodity)) {
                    setCommodity(rows[0].commodity)
                }
            })
            .catch(e => console.error('Failed to load PS&D commodities:', e))
            .finally(() => setLoading(false))
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    // Load attributes when commodity/region change.
    useEffect(() => {
        if (!commodity) return
        api.getPsdAttributes(commodity, region)
            .then(res => {
                const a = (res.data.attributes || []) as AttrRow[]
                setAttrs(a)
                const names = a.map(x => x.attribute)
                // Keep current selection if still valid; else seed with preferred.
                setSelectedAttrs(prev => {
                    const kept = prev.filter(p => names.includes(p))
                    if (kept.length) return kept
                    const seed = PREFERRED_ATTRS.filter(p => names.includes(p)).slice(0, 2)
                    return seed.length ? seed : names.slice(0, 1)
                })
            })
            .catch(e => { console.error('Failed to load attributes:', e); setAttrs([]) })
    }, [commodity, region])

    // Load each selected series.
    useEffect(() => {
        if (!commodity || selectedAttrs.length === 0) { setSeriesMap({}); return }
        let cancelled = false
        Promise.all(selectedAttrs.map(attr =>
            api.getPsdSeries(commodity, attr, region)
                .then(res => [attr, res.data as SeriesPayload] as const)
                .catch(() => [attr, null] as const)
        )).then(pairs => {
            if (cancelled) return
            const m: Record<string, SeriesPayload> = {}
            for (const [attr, payload] of pairs) if (payload) m[attr] = payload
            setSeriesMap(m)
        })
        return () => { cancelled = true }
    }, [commodity, selectedAttrs, region])

    const toggleAttr = (attr: string) => {
        setSelectedAttrs(prev =>
            prev.includes(attr) ? prev.filter(a => a !== attr)
                : prev.length < COLORS.length ? [...prev, attr] : prev)
    }

    // Merge selected series into year-keyed rows for the chart.
    const drawn = selectedAttrs.filter(a => seriesMap[a])
    const rawChartData = useMemo(() => {
        const byYear: Record<number, Record<string, number>> = {}
        for (const attr of drawn) {
            for (const pt of seriesMap[attr].data) {
                byYear[pt.year] ||= { year: pt.year }
                byYear[pt.year][attr] = pt.value
            }
        }
        return Object.values(byYear).sort((a, b) => a.year - b.year)
    }, [drawn, seriesMap])

    const years = distinctYears(rawChartData)
    const chartData = reindexRows(rawChartData, drawn, baseYear)

    // When mixing units, reindex makes the y-axis comparable; otherwise show the unit.
    const units = new Set(drawn.map(a => seriesMap[a]?.unit).filter(Boolean))
    const mixedUnits = units.size > 1
    const unitLabel = baseYear != null
        ? `Index (${baseYear} = 100)`
        : (mixedUnits ? 'Value (mixed units — reindex to compare)' : (drawn[0] ? seriesMap[drawn[0]].unit : 'Value'))

    const anyAggregate = drawn.some(a => seriesMap[a]?.is_aggregate)
    const fileStem = `foodberg_wasde_${commodity.replace(/\W+/g, '_')}_${region === 'World' ? 'world' : 'us'}`

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-ark-fg mb-2 flex items-center">
                    <Wheat className="w-8 h-8 mr-3 text-orange-400" />
                    WASDE Supply &amp; Demand
                </h1>
                <p className="text-ark-fg-dim">
                    Marketing-year supply, use and stocks for major commodities — from the USDA
                    Foreign Agricultural Service PS&amp;D database, the machine-readable balance
                    sheets underlying the WASDE world tables, covering 1960 to present. Every series
                    is multi-decade; gaps are real reporting gaps, never interpolated.
                </p>
            </div>

            {/* Commodity + region pickers */}
            <div className="card mb-6">
                <div className="flex flex-wrap items-end gap-4">
                    <div className="flex-1 min-w-[220px]">
                        <label className="block text-sm text-ark-fg-dim mb-1">Commodity</label>
                        <select
                            value={commodity}
                            onChange={(e) => setCommodity(e.target.value)}
                            className="w-full px-3 py-2 bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg focus:outline-none focus:border-orange-500"
                        >
                            {commodities.map(c => (
                                <option key={c.commodity} value={c.commodity}>
                                    {c.commodity} ({c.min_year}–{c.max_year})
                                </option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm text-ark-fg-dim mb-1">Region</label>
                        <div className="flex gap-2">
                            {(['World', 'United States'] as Region[]).map(r => (
                                <button
                                    key={r}
                                    onClick={() => setRegion(r)}
                                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${region === r
                                        ? 'bg-orange-600 text-white'
                                        : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'}`}
                                >
                                    {r === 'United States' ? 'United States' : 'World'}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Attribute (line item) picker */}
            <div className="card mb-6">
                <h2 className="text-lg font-semibold text-ark-fg mb-3">
                    Balance-sheet line items
                    <span className="text-sm text-ark-fg-dim ml-2">
                        ({drawn.length} drawn · max {COLORS.length})
                    </span>
                </h2>
                <div className="flex flex-wrap gap-2 max-h-44 overflow-y-auto">
                    {attrs.map((a) => {
                        const isSel = selectedAttrs.includes(a.attribute)
                        return (
                            <button
                                key={a.attribute}
                                onClick={() => toggleAttr(a.attribute)}
                                title={`${a.unit} · ${a.min_year}–${a.max_year} (${a.n_years} yrs)`}
                                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${isSel ? 'text-white' : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'}`}
                                style={isSel ? { backgroundColor: COLORS[selectedAttrs.indexOf(a.attribute) % COLORS.length] } : {}}
                                disabled={!isSel && selectedAttrs.length >= COLORS.length}
                            >
                                {a.attribute}
                            </button>
                        )
                    })}
                </div>
            </div>

            {/* Chart */}
            <div className="card">
                <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
                    <h2 className="text-xl font-semibold text-ark-fg">
                        {commodity} — {region === 'World' ? 'World' : 'United States'}
                    </h2>
                    <div className="flex items-center gap-3">
                        <ReindexControl years={years} baseYear={baseYear} onChange={setBaseYear} id="psd-reindex" />
                        <button
                            type="button"
                            className="ark-btn ark-btn-sm ark-btn-ghost"
                            onClick={() => downloadCsv(chartData, fileStem)}
                            disabled={chartData.length === 0}
                        >
                            Download CSV
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="h-[500px] flex items-center justify-center">
                        <div className="animate-spin w-12 h-12 border-2 border-orange-400 border-t-transparent rounded-full"></div>
                    </div>
                ) : chartData.length > 0 && drawn.length > 0 ? (
                    <>
                        <div className="h-[500px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData} margin={{ left: 16, bottom: 8 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={t.gridStroke} />
                                    <XAxis
                                        dataKey="year" stroke={t.axisStroke} tick={{ fill: t.dim }}
                                        label={{ value: 'Marketing year', position: 'insideBottom', offset: -4, fill: t.dim, fontSize: 12 }}
                                    />
                                    <YAxis
                                        stroke={t.axisStroke} tick={{ fill: t.dim }}
                                        tickFormatter={(v) => Number(v).toLocaleString()}
                                        label={{ value: unitLabel, angle: -90, position: 'insideLeft', fill: t.dim, fontSize: 11 }}
                                    />
                                    <Tooltip
                                        contentStyle={t.tooltip}
                                        labelStyle={{ color: t.fg }}
                                        formatter={(value: number, name: string) => [Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 }), name]}
                                        labelFormatter={(label) => `Marketing year ${label}`}
                                    />
                                    <Legend />
                                    {drawn.map((attr) => (
                                        <Line
                                            key={attr}
                                            type="monotone"
                                            dataKey={attr}
                                            stroke={COLORS[selectedAttrs.indexOf(attr) % COLORS.length]}
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
                                source: drawn[0] ? seriesMap[drawn[0]].source : 'USDA FAS PS&D',
                                unit: baseYear != null ? `Index (${baseYear}=100)` : (mixedUnits ? 'mixed' : unitLabel),
                                dateRange: `${Math.min(...years)}–${Math.max(...years)}`,
                                points: chartData.length,
                                note: (anyAggregate && region === 'World'
                                    ? 'World totals are the sum of reported countries (additive attributes only). '
                                    : '')
                                    + 'Marketing-year values; gaps are real reporting gaps, not interpolated. '
                                    + 'Source: USDA FAS Production, Supply & Distribution (apps.fas.usda.gov/psdonline).',
                            }}
                        />

                        <ScrollableDataTable
                            rows={chartData}
                            columns={[
                                { key: 'year', label: 'Marketing year' },
                                ...drawn.map(a => ({ key: a, label: a, numeric: true })),
                            ]}
                            filename={fileStem}
                        />
                    </>
                ) : (
                    <div className="h-[500px] flex items-center justify-center text-ark-fg-dim">
                        <div className="text-center">
                            <Wheat className="w-16 h-16 mx-auto mb-4 text-ark-fg-dim" />
                            <p>Select at least one balance-sheet line item.</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
