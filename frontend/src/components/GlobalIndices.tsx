import { useEffect, useState } from 'react'
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
import { ChartMetaStrip, ScrollableDataTable } from './ChartDetails'

/* Global index families baked from the 2026-06 acquisition:
   - World Bank Pink Sheet index series (food, beverages, agriculture, ...)
     monthly, 1960-present, world level.
   - FAO per-country consumer food price indices (2015=100), monthly,
     ~200 countries, 2000-present.
   One series charted at a time; real rows only. */

interface CatalogIdx { series: string; unit: string; points: number; start: string; end: string }
interface CatalogCpi { country: string; points: number; start: string; end: string }
interface SeriesRow { date: string; value: number }

type Family = 'pinksheet' | 'cpi'

export default function GlobalIndices() {
    const [family, setFamily] = useState<Family>('pinksheet')
    const [pinkCatalog, setPinkCatalog] = useState<CatalogIdx[]>([])
    const [cpiCatalog, setCpiCatalog] = useState<CatalogCpi[]>([])
    const [selected, setSelected] = useState<string | null>(null)
    const [rows, setRows] = useState<SeriesRow[]>([])
    const [meta, setMeta] = useState<{ unit?: string; source?: string }>({})
    const [filter, setFilter] = useState('')
    const [loading, setLoading] = useState(true)
    const t = useArkTheme()

    useEffect(() => {
        api.getGlobalIndices()
            .then((res) => {
                const pink: CatalogIdx[] = res.data.pinksheet_indices || []
                const cpi: CatalogCpi[] = res.data.fao_food_cpi_countries || []
                setPinkCatalog(pink)
                setCpiCatalog(cpi)
                if (pink.length) setSelected(pink[0].series)
            })
            .catch((e) => console.error('Failed to load index catalog:', e))
            .finally(() => setLoading(false))
    }, [])

    useEffect(() => {
        if (!selected) return
        setLoading(true)
        const fetcher = family === 'pinksheet'
            ? api.getPinksheetSeries(selected)
            : api.getCountryCpi(selected)
        fetcher
            .then((res) => {
                setRows(res.data.data || [])
                setMeta({ unit: res.data.unit, source: res.data.source })
            })
            .catch((e) => { console.error(e); setRows([]) })
            .finally(() => setLoading(false))
    }, [selected, family])

    const switchFamily = (f: Family) => {
        setFamily(f)
        setFilter('')
        setSelected(f === 'pinksheet'
            ? (pinkCatalog[0]?.series ?? null)
            : (cpiCatalog.find(c => c.country === 'United States of America')?.country
                ?? cpiCatalog[0]?.country ?? null))
    }

    const options: Array<{ key: string; sub: string }> = family === 'pinksheet'
        ? pinkCatalog.map(p => ({ key: p.series, sub: `${p.start.slice(0, 4)}–${p.end.slice(0, 4)}` }))
        : cpiCatalog.map(c => ({ key: c.country, sub: `${c.start.slice(0, 4)}–${c.end.slice(0, 4)}` }))
    const filtered = options.filter(o => !filter || o.key.toLowerCase().includes(filter.toLowerCase()))

    const chartData = rows.map(r => ({ date: r.date.slice(0, 7), value: r.value }))

    return (
        <div className="card mt-8">
            <h2 className="text-xl font-semibold text-ark-fg mb-1">Global index families</h2>
            <p className="text-sm text-ark-fg-dim mb-4">
                World Bank Pink Sheet commodity-group indices (monthly, world level) and FAO
                consumer food price indices per country (2015=100, monthly).
            </p>

            <div className="flex gap-2 mb-4 flex-wrap">
                <button
                    onClick={() => switchFamily('pinksheet')}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${family === 'pinksheet'
                        ? 'bg-emerald-600 text-white' : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'}`}
                >
                    Pink Sheet indices ({pinkCatalog.length})
                </button>
                <button
                    onClick={() => switchFamily('cpi')}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${family === 'cpi'
                        ? 'bg-emerald-600 text-white' : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'}`}
                >
                    Country food CPI ({cpiCatalog.length})
                </button>
                {options.length > 25 && (
                    <input
                        type="text"
                        placeholder="Filter…"
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="px-3 py-1.5 bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg placeholder-ark-fg-dim focus:outline-none focus:border-emerald-500"
                    />
                )}
            </div>

            <div className="flex flex-wrap gap-2 mb-4 max-h-36 overflow-y-auto">
                {filtered.slice(0, 100).map(o => (
                    <button
                        key={o.key}
                        onClick={() => setSelected(o.key)}
                        title={o.sub}
                        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${selected === o.key
                            ? 'bg-emerald-600 text-white' : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'}`}
                    >
                        {o.key}
                    </button>
                ))}
            </div>

            {loading ? (
                <div className="h-[320px] flex items-center justify-center text-ark-fg-dim">Loading…</div>
            ) : chartData.length > 1 ? (
                <>
                    <div className="h-[320px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData} margin={{ left: 12, bottom: 8 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke={t.gridStroke} />
                                <XAxis dataKey="date" stroke={t.axisStroke} tick={{ fill: t.dim }} minTickGap={40} />
                                <YAxis stroke={t.axisStroke} tick={{ fill: t.dim }}
                                    tickFormatter={(v) => v.toLocaleString()}
                                    label={{ value: meta.unit || 'Index', angle: -90, position: 'insideLeft', fill: t.dim, fontSize: 11 }} />
                                <Tooltip
                                    contentStyle={t.tooltip}
                                    labelStyle={{ color: t.fg }}
                                    formatter={(value: number) => [value.toLocaleString(undefined, { maximumFractionDigits: 2 }), meta.unit || 'value']}
                                />
                                <Line type="monotone" dataKey="value" stroke={t.accent} strokeWidth={2} dot={false} activeDot={{ r: 5 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                    <ChartMetaStrip
                        meta={{
                            source: meta.source,
                            unit: meta.unit,
                            dateRange: `${chartData[0].date} → ${chartData[chartData.length - 1].date}`,
                            points: chartData.length,
                        }}
                    />
                    <ScrollableDataTable
                        rows={chartData}
                        columns={[{ key: 'date', label: 'Month' }, { key: 'value', label: meta.unit || 'Value', numeric: true }]}
                        filename={`foodberg_index_${(selected || '').replace(/\W+/g, '_')}`}
                        maxHeight={240}
                    />
                </>
            ) : (
                <div className="h-[320px] flex items-center justify-center text-ark-fg-dim">
                    No series selected (or no data for this selection).
                </div>
            )}
        </div>
    )
}
