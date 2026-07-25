import { Wheat } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../services/api'
import {
    CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
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

// --- Vintages types ---
interface VintageRow {
    report_date: string
    release_date: string
    wasde_number: number
    value: number
    unit: string
    proj_est_flag: string | null
}

interface VintageSeriesPayload {
    commodity: string
    region: string
    attribute: string
    market_year: string
    n_reports: number
    units_used: string[]
    note: string | null
    data: VintageRow[]
}

interface MarketYearRow {
    market_year: string
    report_count: number
    first_report: string
    last_report: string
    n_attributes: number
}

// --- Legacy types ---
interface LegacyCommodityRow {
    commodity: string
    row_count: number
    n_attributes: number
    min_year: string
    max_year: string
}

interface LegacyCoveragePayload {
    source: string
    disclaimer: string
    per_decade_totals: Array<{ decade: string; attributed: number; total_rows: number; clean_pct: number }>
    coverage_matrix: Record<string, Record<string, {
        attributed_rows: number; min_my: string; max_my: string; n_attributes: number; n_regions: number
    }>>
}

interface LegacySeriesPayload {
    commodity: string
    region: string
    attribute_filter: string | null
    available_attributes: string[]
    n_rows: number
    year_range: { start: string; end: string }
    disclaimer: string
    data: Array<{ market_year: string; value: number; unit: string; attribute: string; region: string; attribution_label: string }>
}

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

    // --- Vintages state ---
    const [vintagesAttr, setVintagesAttr] = useState<string>('Production')
    const [vintagesMY, setVintagesMY] = useState<string>('')
    const [vintagesMYs, setVintagesMYs] = useState<MarketYearRow[]>([])
    const [vintagesAttrs, setVintagesAttrs] = useState<string[]>([])
    const [vintagesRegions, setVintagesRegions] = useState<string[]>([])
    const [vintagesRegion, setVintagesRegion] = useState<string>('United States')
    const [vintagesPayload, setVintagesPayload] = useState<VintageSeriesPayload | null>(null)
    const [vintagesLoading, setVintagesLoading] = useState(false)
    const [vintagesMounted, setVintagesMounted] = useState(false)  // lazy-load chart on tab open

    // --- Legacy state ---
    const [legacyCommodities, setLegacyCommodities] = useState<LegacyCommodityRow[]>([])
    const [legacyCommodity, setLegacyCommodity] = useState<string>('Cotton')
    const [legacyRegion, setLegacyRegion] = useState<string>('World')
    const [legacyAttr, setLegacyAttr] = useState<string>('')
    const [legacyAttrs, setLegacyAttrs] = useState<string[]>([])
    const [legacyRegions, setLegacyRegions] = useState<string[]>(['World'])
    const [legacyPayload, setLegacyPayload] = useState<LegacySeriesPayload | null>(null)
    const [legacyCoverage, setLegacyCoverage] = useState<LegacyCoveragePayload | null>(null)
    const [legacyLoading, setLegacyLoading] = useState(false)
    const [legacyMounted, setLegacyMounted] = useState(false)

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

    // Load vintages attributes/market-years when commodity changes.
    useEffect(() => {
        if (!commodity || !vintagesMounted) return
        setVintagesLoading(true)
        Promise.all([
            api.getVintagesAttributes(commodity).then(r => r.data).catch(() => null),
            api.getVintagesMarketYears(commodity).then(r => r.data).catch(() => null),
        ]).then(([attrData, myData]) => {
            if (attrData) {
                setVintagesAttrs(attrData.attributes || [])
                setVintagesRegions(attrData.regions || [])
                if (!attrData.attributes.includes(vintagesAttr) && attrData.attributes.length > 0) {
                    setVintagesAttr(attrData.attributes[0])
                }
                if (!attrData.regions.includes(vintagesRegion) && attrData.regions.length > 0) {
                    setVintagesRegion(attrData.regions[0])
                }
            }
            if (myData) {
                setVintagesMYs(myData.market_years || [])
                if (!myData.market_years?.find((m: MarketYearRow) => m.market_year === vintagesMY)) {
                    setVintagesMY(myData.market_years?.[0]?.market_year || '')
                }
            }
        }).finally(() => setVintagesLoading(false))
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [commodity, vintagesMounted])

    // Load vintages series when attr/market_year/region change.
    useEffect(() => {
        if (!commodity || !vintagesAttr || !vintagesMY || !vintagesRegion || !vintagesMounted) {
            setVintagesPayload(null)
            return
        }
        setVintagesPayload(null)
        api.getVintagesSeries(commodity, vintagesAttr, vintagesRegion, vintagesMY)
            .then(res => setVintagesPayload(res.data as VintageSeriesPayload))
            .catch(() => setVintagesPayload(null))
    }, [commodity, vintagesAttr, vintagesMY, vintagesRegion, vintagesMounted])

    // Load legacy commodity list + coverage when tab is first opened.
    useEffect(() => {
        if (!legacyMounted) return
        setLegacyLoading(true)
        Promise.all([
            api.getLegacyCommodities().then(r => r.data).catch(() => null),
            api.getLegacyCoverage().then(r => r.data).catch(() => null),
        ]).then(([commData, covData]) => {
            if (commData?.commodities?.length) {
                const comms = commData.commodities as LegacyCommodityRow[]
                setLegacyCommodities(comms)
                if (!comms.find(c => c.commodity === legacyCommodity)) {
                    setLegacyCommodity(comms[0].commodity)
                }
            }
            if (covData) setLegacyCoverage(covData as LegacyCoveragePayload)
        }).finally(() => setLegacyLoading(false))
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [legacyMounted])

    // Load legacy series when commodity/region/attr change.
    useEffect(() => {
        if (!legacyCommodity || !legacyMounted) { setLegacyPayload(null); return }
        setLegacyPayload(null)
        api.getLegacySeries(legacyCommodity, legacyRegion, legacyAttr || undefined)
            .then(res => {
                const p = res.data as LegacySeriesPayload
                setLegacyPayload(p)
                // Derive available regions by scanning data
                const regs = new Set<string>()
                const attrs = new Set<string>()
                for (const r of p.data) {
                    if (r.region) regs.add(r.region)
                    attrs.add(r.attribute)
                }
                setLegacyRegions(Array.from(regs).sort())
                const attrArr = Array.from(attrs).sort()
                setLegacyAttrs(attrArr)
                if (!attrArr.includes(legacyAttr)) {
                    setLegacyAttr(attrArr[0] || '')
                }
            })
            .catch(() => setLegacyPayload(null))
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [legacyCommodity, legacyRegion, legacyAttr, legacyMounted])

    // Chart-friendly: group legacy data by attribute, keyed by market_year
    const legacyChartData = useMemo(() => {
        if (!legacyPayload?.data) return { rows: [], attrs: [] as string[], mode: 'empty' as const }
        if (legacyAttr) {
            const single = legacyPayload.data
                .filter(r => r.attribute === legacyAttr)
                .map(r => ({ label: r.market_year, value: r.value, unit: r.unit }))
                .sort((a, b) => a.label.localeCompare(b.label))
            return { rows: single, attrs: [legacyAttr], mode: 'single' as const }
        }
        const byYear: Record<string, any> = {}
        const unitMap: Record<string, string> = {}
        const attrSet = new Set<string>()
        for (const r of legacyPayload.data) {
            byYear[r.market_year] ||= { label: r.market_year }
            byYear[r.market_year][r.attribute] = r.value
            unitMap[r.attribute] = r.unit
            attrSet.add(r.attribute)
        }
        const attrs = Array.from(attrSet).sort()
        return { rows: Object.values(byYear).sort((a: any, b: any) => String(a.label).localeCompare(String(b.label))), attrs, mode: 'multi' as const }
    }, [legacyPayload, legacyAttr])

    // Chart-friendly rows: sort by release_date, keep report_date for labels.
    const vintagesChartData = useMemo(() => {
        if (!vintagesPayload?.data) return []
        return vintagesPayload.data
            .map(r => ({
                label: r.report_date,
                value: r.value,
                unit: r.unit,
                wasde_number: r.wasde_number,
            }))
    }, [vintagesPayload])

    const vintagesFinalValue = useMemo(() => {
        if (vintagesChartData.length === 0) return null
        return vintagesChartData[vintagesChartData.length - 1].value
    }, [vintagesChartData])

    const vintagesMixedUnits = useMemo(() => {
        const u = new Set(vintagesChartData.map(r => r.unit))
        return u.size > 1
    }, [vintagesChartData])

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

            {/* Tab toggle: Balance Sheet vs. Vintages */}
            <div className="flex gap-3 mb-6">
                <button
                    onClick={() => { setVintagesMounted(false) }}
                    className={`px-5 py-2 rounded-lg font-medium text-sm transition-colors ${!vintagesMounted ? 'bg-orange-600 text-white' : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'}`}
                >
                    Balance Sheet
                </button>
                <button
                    onClick={() => { setVintagesMounted(true); setLegacyMounted(false) }}
                    className={`px-5 py-2 rounded-lg font-medium text-sm transition-colors ${vintagesMounted && !legacyMounted ? 'bg-orange-600 text-white' : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'}`}
                >
                    WASDE Vintages
                </button>
                <button
                    onClick={() => { setLegacyMounted(true); setVintagesMounted(false) }}
                    className={`px-5 py-2 rounded-lg font-medium text-sm transition-colors ${legacyMounted ? 'bg-orange-600 text-white' : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'}`}
                >
                    Legacy (1979–2009)
                </button>
            </div>

            {!vintagesMounted && !legacyMounted ? (
                <>
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

            {/* PS&D Chart */}
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
                </>
            ) : vintagesMounted ? (
                <>
            {/* Vintages pickers */}
            <div className="card mb-6">
                <div className="flex flex-wrap items-end gap-4">
                    <div>
                        <label className="block text-sm text-ark-fg-dim mb-1">Attribute</label>
                        <select
                            value={vintagesAttr}
                            onChange={e => setVintagesAttr(e.target.value)}
                            className="px-3 py-2 bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg focus:outline-none focus:border-orange-500"
                        >
                            {vintagesAttrs.map(a => (<option key={a} value={a}>{a}</option>))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm text-ark-fg-dim mb-1">Region</label>
                        <select
                            value={vintagesRegion}
                            onChange={e => setVintagesRegion(e.target.value)}
                            className="px-3 py-2 bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg focus:outline-none focus:border-orange-500"
                        >
                            {vintagesRegions.map(r => (<option key={r} value={r}>{r}</option>))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm text-ark-fg-dim mb-1">Market Year</label>
                        <select
                            value={vintagesMY}
                            onChange={e => setVintagesMY(e.target.value)}
                            className="px-3 py-2 bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg focus:outline-none focus:border-orange-500"
                        >
                            {vintagesMYs.map(m => (
                                <option key={m.market_year} value={m.market_year}>
                                    {m.market_year} ({m.report_count} reports)
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            {/* Vintages trajectory chart */}
            <div className="card">
                <h2 className="text-xl font-semibold text-ark-fg mb-1">
                    {commodity} {vintagesAttr} — {vintagesMY} ({vintagesRegion})
                </h2>
                <p className="text-sm text-ark-fg-dim mb-4">
                    As-reported WASDE estimates over time: each point is what one report said.
                    {vintagesMixedUnits && (
                        <span className="text-orange-400 ml-2 font-medium">
                            ⚠ Units changed across the reporting window; each point carries its own unit — see tooltip.
                        </span>
                    )}
                </p>

                {vintagesLoading ? (
                    <div className="h-[450px] flex items-center justify-center">
                        <div className="animate-spin w-12 h-12 border-2 border-orange-400 border-t-transparent rounded-full"></div>
                    </div>
                ) : vintagesChartData.length > 0 ? (
                    <>
                        <div className="h-[450px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={vintagesChartData} margin={{ left: 16, bottom: 8 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={t.gridStroke} />
                                    <XAxis
                                        dataKey="label" stroke={t.axisStroke} tick={{ fill: t.dim, fontSize: 11 }}
                                        interval="preserveStartEnd"
                                        label={{ value: 'WASDE report date', position: 'insideBottom', offset: -4, fill: t.dim, fontSize: 12 }}
                                    />
                                    <YAxis
                                        stroke={t.axisStroke} tick={{ fill: t.dim }}
                                        tickFormatter={(v) => Number(v).toLocaleString()}
                                        label={{ value: vintagesMixedUnits ? 'Value (mixed units — see note)' : (vintagesChartData[0]?.unit || 'Value'), angle: -90, position: 'insideLeft', fill: t.dim, fontSize: 11 }}
                                    />
                                    <Tooltip
                                        contentStyle={t.tooltip}
                                        labelStyle={{ color: t.fg }}
                                        formatter={(value: number, _name: string, props: any) => [
                                            `${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })} ${props.payload.unit || ''}`,
                                            `WASDE #${props.payload.wasde_number || '?'}`,
                                        ]}
                                        labelFormatter={(label) => `Report: ${label}`}
                                    />
                                    <Legend />
                                    <Line
                                        type="stepAfter"
                                        dataKey="value"
                                        stroke="#F59E0B"
                                        strokeWidth={2.5}
                                        dot={{ r: 3 }}
                                        name={vintagesAttr}
                                        connectNulls
                                    />
                                    {vintagesFinalValue != null && (
                                        <ReferenceLine
                                            y={vintagesFinalValue}
                                            stroke="#6B7280"
                                            strokeDasharray="6 3"
                                            label={{ value: `Final: ${Number(vintagesFinalValue).toLocaleString()}`, fill: t.dim, fontSize: 11, position: 'right' }}
                                        />
                                    )}
                                </LineChart>
                            </ResponsiveContainer>
                        </div>

                        <ChartMetaStrip
                            meta={{
                                source: 'USDA WASDE',
                                unit: vintagesMixedUnits ? 'mixed — see data table' : (vintagesChartData[0]?.unit || ''),
                                dateRange: `${vintagesChartData[0]?.label} — ${vintagesChartData[vintagesChartData.length - 1]?.label}`,
                                points: vintagesChartData.length,
                                note: (vintagesPayload?.note || '')
                                    + ' Each point is what one WASDE report estimated. '
                                    + 'Units may change across the reporting history — every row carries its own unit. '
                                    + 'Source: USDA WASDE reports (usda.gov/oce/commodity/wasde).',
                            }}
                        />

                        <ScrollableDataTable
                            rows={vintagesChartData}
                            columns={[
                                { key: 'label', label: 'Report date' },
                                { key: 'wasde_number', label: 'WASDE #' },
                                { key: 'value', label: 'Value', numeric: true },
                                { key: 'unit', label: 'Unit' },
                            ]}
                            filename={`foodberg_vintages_${commodity.replace(/\W+/g, '_')}_${vintagesAttr}_${vintagesMY.replace(/\W+/g, '_')}`}
                        />
                    </>
                ) : (
                    <div className="h-[450px] flex items-center justify-center text-ark-fg-dim">
                        <div className="text-center">
                            <Wheat className="w-16 h-16 mx-auto mb-4 text-ark-fg-dim" />
                            <p>Select attribute, region and market year to view revision history.</p>
                        </div>
                    </div>
                )}
            </div>
                </>
            ) : (
                <>
            {/* Legacy pickers */}
            <div className="card mb-6">
                <div className="flex flex-wrap items-end gap-4">
                    <div className="flex-1 min-w-[220px]">
                        <label className="block text-sm text-ark-fg-dim mb-1">Commodity</label>
                        <select
                            value={legacyCommodity}
                            onChange={e => setLegacyCommodity(e.target.value)}
                            className="w-full px-3 py-2 bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg focus:outline-none focus:border-orange-500"
                        >
                            {legacyCommodities.map(c => (
                                <option key={c.commodity} value={c.commodity}>
                                    {c.commodity} ({c.min_year}–{c.max_year}, {c.row_count.toLocaleString()} rows)
                                </option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm text-ark-fg-dim mb-1">Region</label>
                        <select
                            value={legacyRegion}
                            onChange={e => setLegacyRegion(e.target.value)}
                            className="px-3 py-2 bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg focus:outline-none focus:border-orange-500"
                        >
                            {legacyRegions.map(r => (<option key={r} value={r}>{r}</option>))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm text-ark-fg-dim mb-1">Attribute</label>
                        <select
                            value={legacyAttr}
                            onChange={e => setLegacyAttr(e.target.value)}
                            className="px-3 py-2 bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg focus:outline-none focus:border-orange-500"
                        >
                            <option value="">All attributes</option>
                            {legacyAttrs.map(a => (<option key={a} value={a}>{a}</option>))}
                        </select>
                    </div>
                </div>
            </div>

            {/* Coverage label */}
            {legacyCoverage && legacyCommodity && legacyCoverage.coverage_matrix[legacyCommodity] && (
                <div className="card mb-6 bg-amber-900/20 border-amber-700/50">
                    <h3 className="text-sm font-semibold text-amber-700 dark:text-amber-300 mb-2">Coverage note</h3>
                    <p className="text-sm text-amber-900/80 dark:text-amber-200/80 leading-relaxed">
                        Machine-extracted from historical USDA WASDE reports, 1979–2009, partial coverage.
                        {Object.entries(legacyCoverage.coverage_matrix[legacyCommodity]).map(([decade, info]) => (
                            <span key={decade} className="ml-2">
                                {decade}: {info.attributed_rows.toLocaleString()} rows
                                ({info.min_my}–{info.max_my})
                            </span>
                        ))}
                        <span className="block mt-1 text-xs text-amber-700 dark:text-amber-700/70 dark:text-amber-300/60">
                            Units as printed per row. Gaps are real extraction gaps — no interpolation.
                            <a href="/docs/provenance" className="underline ml-1">See provenance →</a>
                        </span>
                    </p>
                </div>
            )}

            {/* Legacy chart */}
            <div className="card">
                <h2 className="text-xl font-semibold text-ark-fg mb-1">
                    {legacyCommodity} — {legacyRegion}
                    {legacyAttr ? ` · ${legacyAttr}` : ''}
                </h2>
                <p className="text-sm text-ark-fg-dim mb-4">
                    {legacyPayload?.disclaimer || 'Machine-extracted historical WASDE data (1979–2009).'}
                </p>

                {legacyLoading ? (
                    <div className="h-[450px] flex items-center justify-center">
                        <div className="animate-spin w-12 h-12 border-2 border-orange-400 border-t-transparent rounded-full"></div>
                    </div>
                ) : legacyPayload && legacyChartData.rows.length > 0 ? (
                    <>
                        <div className="h-[450px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={legacyChartData.rows} margin={{ left: 16, bottom: 8 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={t.gridStroke} />
                                    <XAxis
                                        dataKey="label" stroke={t.axisStroke} tick={{ fill: t.dim, fontSize: 11 }}
                                        interval="preserveStartEnd"
                                        label={{ value: 'Marketing year', position: 'insideBottom', offset: -4, fill: t.dim, fontSize: 12 }}
                                    />
                                    <YAxis
                                        stroke={t.axisStroke} tick={{ fill: t.dim }}
                                        tickFormatter={(v) => Number(v).toLocaleString()}
                                        label={{ value: legacyChartData.mode === 'single' ? (legacyChartData.rows[0]?.unit || 'Value') : 'Value (units vary — see tooltip)', angle: -90, position: 'insideLeft', fill: t.dim, fontSize: 11 }}
                                    />
                                    <Tooltip
                                        contentStyle={t.tooltip}
                                        labelStyle={{ color: t.fg }}
                                        formatter={(value: number, name: string) => [
                                            Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 }),
                                            name,
                                        ]}
                                        labelFormatter={(label) => `MY ${label}`}
                                    />
                                    <Legend />
                                    {legacyChartData.mode === 'single' ? (
                                        <Line
                                            type="monotone"
                                            dataKey="value"
                                            stroke="#8B5CF6"
                                            strokeWidth={2.5}
                                            dot={{ r: 3 }}
                                            name={legacyChartData.attrs[0]}
                                            connectNulls={false}
                                        />
                                    ) : (
                                        legacyChartData.attrs.map((attr, idx) => (
                                            <Line
                                                key={attr}
                                                type="monotone"
                                                dataKey={attr}
                                                stroke={COLORS[idx % COLORS.length]}
                                                strokeWidth={2}
                                                dot={false}
                                                activeDot={{ r: 6 }}
                                                name={attr}
                                                connectNulls={false}
                                            />
                                        ))
                                    )}
                                </LineChart>
                            </ResponsiveContainer>
                        </div>

                        <ChartMetaStrip
                            meta={{
                                source: 'USDA WASDE (machine-extracted from historical PDFs)',
                                unit: legacyChartData.mode === 'single' ? (legacyChartData.rows[0]?.unit || '') : 'mixed — see data table',
                                dateRange: `${legacyPayload.year_range.start} — ${legacyPayload.year_range.end}`,
                                points: legacyPayload.n_rows,
                                note: (legacyPayload.disclaimer || '')
                                    + ' Machine-extracted from historical reports. '
                                    + 'Units as printed per row — no conversion. '
                                    + 'Gaps are real extraction gaps, never interpolated.',
                            }}
                        />

                        <ScrollableDataTable
                            rows={legacyChartData.rows}
                            columns={
                                legacyChartData.mode === 'single'
                                    ? [
                                        { key: 'label', label: 'Marketing year' },
                                        { key: 'value', label: legacyChartData.attrs[0], numeric: true },
                                        { key: 'unit', label: 'Unit' },
                                    ]
                                    : [
                                        { key: 'label', label: 'Marketing year' },
                                        ...legacyChartData.attrs.map(a => ({ key: a, label: a, numeric: true })),
                                    ]
                            }
                            filename={`foodberg_legacy_${legacyCommodity.replace(/\W+/g, '_')}_${legacyRegion.replace(/\W+/g, '_')}`}
                        />
                    </>
                ) : (
                    <div className="h-[450px] flex items-center justify-center text-ark-fg-dim">
                        <div className="text-center">
                            <Wheat className="w-16 h-16 mx-auto mb-4 text-ark-fg-dim" />
                            <p>Select a commodity and region to view legacy data.</p>
                        </div>
                    </div>
                )}
            </div>
                </>
            )}
        </div>
    )
}
