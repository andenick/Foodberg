import { Globe, MapPin } from 'lucide-react'
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
import { downloadCsv, useArkTheme } from '../arcanum/arkChartTheme'
import { ChartMetaStrip, ScrollableDataTable } from '../components/ChartDetails'

// Color palette for multiple lines
const COLORS = [
    '#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
]

type Mode = 'producer' | 'states' | 'indicators'

interface GeoSeries {
    unit: string | null
    regions: string[]
    n_obs: number
    year_range: { start: number; end: number }
    data: Array<{ region: string; year: number; value: number }>
    source: string
    name?: string
    item?: string
    commodity?: string
}

interface PickerEntry {
    key: string
    label: string
    sub?: string
}

const MODE_INFO: Record<Mode, { title: string; blurb: string }> = {
    producer: {
        title: 'Producer prices by country',
        blurb: 'FAOSTAT farm-gate producer prices in USD/tonne — annual, per country, 1991–2024.',
    },
    states: {
        title: 'US state farm prices',
        blurb: 'USDA NASS prices received by farmers, per state — annual, 1950–present.',
    },
    indicators: {
        title: 'Development indicators',
        blurb: 'World Bank agriculture and food indicators — annual, 1990–2024, nine world regions.',
    },
}

// US-state-capable commodities (the top-15 with state-level NASS history).
const STATE_COMMODITIES = [
    'wheat', 'corn', 'soybeans', 'cotton', 'rice', 'barley', 'oats',
    'sorghum', 'hay', 'cattle', 'hogs', 'milk', 'eggs', 'potatoes', 'peanuts',
]

const DEFAULT_REGIONS: Record<Mode, string[]> = {
    producer: ['United States of America', 'China, mainland', 'Brazil'],
    states: ['KANSAS', 'ILLINOIS', 'TEXAS'],
    indicators: ['United States', 'China', 'Brazil'],
}

export default function GeographicPrices() {
    const [mode, setMode] = useState<Mode>('producer')
    const [picker, setPicker] = useState<PickerEntry[]>([])
    const [selectedKey, setSelectedKey] = useState<string | null>(null)
    const [series, setSeries] = useState<GeoSeries | null>(null)
    const [selectedRegions, setSelectedRegions] = useState<string[]>(DEFAULT_REGIONS.producer)
    const [regionFilter, setRegionFilter] = useState('')
    // The producer-price picker carries ~185 FAOSTAT items. Rendered as a flat,
    // unfiltered wall of buttons in a short scroll box, roughly 25 fresh
    // vegetables — tomatoes among them — were present but effectively
    // unfindable. A filter box makes the already-loaded data reachable.
    const [itemFilter, setItemFilter] = useState('')
    const [loading, setLoading] = useState(true)
    const t = useArkTheme()

    // Load the picker list whenever the mode changes.
    useEffect(() => {
        setLoading(true)
        setSeries(null)
        setSelectedKey(null)
        setSelectedRegions(DEFAULT_REGIONS[mode])
        setRegionFilter('')
        setItemFilter('')
        const load = async () => {
            try {
                if (mode === 'producer') {
                    const res = await api.getProducerItems()
                    const items = (res.data.items || []) as Array<{ item: string; n_countries: number; year_start: number; year_end: number }>
                    setPicker(items.map(i => ({
                        key: i.item, label: i.item,
                        sub: `${i.n_countries} countries · ${i.year_start}–${i.year_end}`,
                    })))
                    if (items.length) setSelectedKey(items[0].item)
                } else if (mode === 'states') {
                    setPicker(STATE_COMMODITIES.map(c => ({ key: c, label: c })))
                    setSelectedKey(STATE_COMMODITIES[0])
                } else {
                    const res = await api.getGeoIndicators()
                    const inds = (res.data.indicators || []) as Array<{ indicator_code: string; name: string; year_start: number; year_end: number; n_regions: number }>
                    setPicker(inds.map(i => ({
                        key: i.indicator_code, label: i.name,
                        sub: `${i.year_start}–${i.year_end} · ${i.n_regions} regions`,
                    })))
                    if (inds.length) setSelectedKey(inds[0].indicator_code)
                }
            } catch (e) {
                console.error('Failed to load picker:', e)
            } finally {
                setLoading(false)
            }
        }
        load()
    }, [mode])

    // Load the series whenever the selected item changes.
    useEffect(() => {
        if (!selectedKey) return
        setLoading(true)
        const load = async () => {
            try {
                const res = mode === 'producer'
                    ? await api.getProducerSeries(selectedKey)
                    : mode === 'states'
                        ? await api.getStateSeries(selectedKey)
                        : await api.getGeoSeries(selectedKey)
                setSeries(res.data.status === 'data_unavailable' ? null : res.data)
            } catch (e) {
                console.error('Failed to load series:', e)
                setSeries(null)
            } finally {
                setLoading(false)
            }
        }
        load()
    }, [selectedKey, mode])

    const toggleRegion = (region: string) => {
        if (selectedRegions.includes(region)) {
            setSelectedRegions(selectedRegions.filter(r => r !== region))
        } else if (selectedRegions.length < 6) {
            setSelectedRegions([...selectedRegions, region])
        }
    }

    const regionsWithData = new Set(series?.regions ?? [])
    const drawnRegions = selectedRegions.filter(r => regionsWithData.has(r))
    const missingRegions = selectedRegions.filter(r => !regionsWithData.has(r))

    const chartData = (() => {
        if (!series) return []
        const byYear: Record<number, Record<string, number | string>> = {}
        for (const row of series.data) {
            if (!drawnRegions.includes(row.region)) continue
            byYear[row.year] ||= { year: row.year }
            byYear[row.year][row.region] = row.value
        }
        return Object.values(byYear).sort((a, b) => (a.year as number) - (b.year as number))
    })()

    const filteredPicker = picker.filter(p => {
        const needle = itemFilter.trim().toLowerCase()
        if (!needle) return true
        return p.label.toLowerCase().includes(needle)
            || p.key.toLowerCase().includes(needle)
    })

    const unitLabel = series?.unit || 'Value'
    const filteredRegions = (series?.regions ?? []).filter(
        r => !regionFilter || r.toLowerCase().includes(regionFilter.toLowerCase()))
    const seriesTitle = series?.item || series?.name
        || (series?.commodity ? `${series.commodity} — state farm prices` : 'Series')

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-ark-fg mb-2 flex items-center">
                    <Globe className="w-8 h-8 mr-3 text-blue-400" />
                    Geographic Comparison
                </h1>
                <p className="text-ark-fg-dim">
                    Compare real food prices and indicators across geographies — FAOSTAT producer
                    prices by country, USDA farm prices by US state, and World Bank development
                    indicators by region. All series are baked locally; gaps are real reporting
                    gaps, never interpolated.
                </p>
            </div>

            {/* Mode toggle */}
            <div className="card mb-6">
                <div className="flex flex-wrap gap-2">
                    {(Object.keys(MODE_INFO) as Mode[]).map(m => (
                        <button
                            key={m}
                            onClick={() => setMode(m)}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${mode === m
                                ? 'bg-emerald-600 text-white'
                                : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                }`}
                        >
                            {MODE_INFO[m].title}
                        </button>
                    ))}
                </div>
                <p className="text-sm text-ark-fg-dim mt-3">{MODE_INFO[mode].blurb}</p>
            </div>

            {/* Item picker */}
            <div className="card mb-6">
                <div className="flex items-center justify-between flex-wrap gap-2 mb-4">
                    <h2 className="text-lg font-semibold text-ark-fg capitalize">
                        Select {mode === 'indicators' ? 'indicator' : 'commodity'}
                        <span className="text-sm text-ark-fg-dim ml-2">
                            ({filteredPicker.length}
                            {filteredPicker.length !== picker.length ? ` of ${picker.length}` : ''} available)
                        </span>
                    </h2>
                    {picker.length > 20 && (
                        <input
                            type="text"
                            placeholder={mode === 'producer'
                                ? 'Filter items — try “tomato”, “lettuce”, “onion”…'
                                : 'Filter…'}
                            value={itemFilter}
                            onChange={(e) => setItemFilter(e.target.value)}
                            className="px-3 py-1.5 min-w-[16rem] bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg placeholder-ark-fg-dim focus:outline-none focus:border-emerald-500"
                        />
                    )}
                </div>
                {filteredPicker.length === 0 ? (
                    <p className="text-sm text-ark-fg-dim py-2">
                        No item matches “{itemFilter.trim()}”. There are {picker.length} items in
                        this source; the filter searches all of them.
                    </p>
                ) : (
                    <div className="flex flex-wrap gap-2 max-h-72 overflow-y-auto">
                        {filteredPicker.map(p => (
                            <button
                                key={p.key}
                                onClick={() => setSelectedKey(p.key)}
                                title={p.sub}
                                className={`px-3 py-2 rounded-lg text-left text-sm font-medium capitalize transition-colors ${selectedKey === p.key
                                    ? 'bg-emerald-600 text-white'
                                    : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                    }`}
                            >
                                <span className="block">{p.label}</span>
                                {p.sub && (
                                    <span className={`block text-[10px] normal-case mt-0.5 ${selectedKey === p.key ? 'text-emerald-100' : 'text-ark-fg-dim'
                                        }`}>
                                        {p.sub}
                                    </span>
                                )}
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Region picker */}
            <div className="card mb-6">
                <div className="flex items-center justify-between flex-wrap gap-2 mb-4">
                    <h2 className="text-lg font-semibold text-ark-fg">
                        Select regions (max 6)
                        <span className="text-sm text-ark-fg-dim ml-2">
                            ({drawnRegions.length} drawn{missingRegions.length ? `, ${missingRegions.length} without data` : ''})
                        </span>
                    </h2>
                    {(series?.regions.length ?? 0) > 25 && (
                        <input
                            type="text"
                            placeholder="Filter regions…"
                            value={regionFilter}
                            onChange={(e) => setRegionFilter(e.target.value)}
                            className="px-3 py-1.5 bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg placeholder-ark-fg-dim focus:outline-none focus:border-emerald-500"
                        />
                    )}
                </div>

                {series ? (
                    <>
                        <div className="flex flex-wrap gap-2 max-h-44 overflow-y-auto">
                            {filteredRegions.slice(0, 120).map((region) => (
                                <button
                                    key={region}
                                    onClick={() => toggleRegion(region)}
                                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center capitalize ${selectedRegions.includes(region)
                                        ? 'text-white'
                                        : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                        }`}
                                    style={selectedRegions.includes(region) ? {
                                        backgroundColor: COLORS[selectedRegions.indexOf(region) % COLORS.length]
                                    } : {}}
                                    disabled={!selectedRegions.includes(region) && selectedRegions.length >= 6}
                                >
                                    <MapPin className="w-3 h-3 mr-1" />
                                    {region.toLowerCase()}
                                </button>
                            ))}
                        </div>
                        {missingRegions.length > 0 && (
                            <p className="text-xs text-amber-400/80 mt-3">
                                No data for this selection: {missingRegions.join(', ')} — deselect or pick another item.
                            </p>
                        )}
                    </>
                ) : (
                    <p className="text-ark-fg-dim">Loading available regions...</p>
                )}
            </div>

            <div className="card">
                <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
                    <h2 className="text-xl font-semibold text-ark-fg capitalize">{seriesTitle}</h2>
                    <button
                        type="button"
                        className="ark-btn ark-btn-sm ark-btn-ghost"
                        onClick={() => downloadCsv(chartData, `foodberg_geo_${mode}_${(selectedKey || '').replace(/\W+/g, '_')}`)}
                        disabled={chartData.length === 0}
                    >
                        Download CSV
                    </button>
                </div>

                {loading ? (
                    <div className="h-[500px] flex items-center justify-center">
                        <div className="text-center">
                            <div className="animate-spin w-12 h-12 border-2 border-emerald-400 border-t-transparent rounded-full mx-auto"></div>
                            <p className="text-ark-fg-dim mt-4">Loading data...</p>
                        </div>
                    </div>
                ) : chartData.length > 0 ? (
                    <>
                        <div className="h-[500px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData} margin={{ left: 16, bottom: 8 }}>
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
                                        label={{ value: unitLabel, angle: -90, position: 'insideLeft', fill: t.dim, fontSize: 11 }}
                                    />
                                    <Tooltip
                                        contentStyle={t.tooltip}
                                        labelStyle={{ color: t.fg }}
                                        formatter={(value: number, name: string) => [value.toLocaleString(undefined, { maximumFractionDigits: 2 }), name]}
                                        labelFormatter={(label) => `Year ${label}`}
                                    />
                                    <Legend />
                                    {drawnRegions.map((region) => (
                                        <Line
                                            key={region}
                                            type="monotone"
                                            dataKey={region}
                                            stroke={COLORS[selectedRegions.indexOf(region) % COLORS.length]}
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
                                source: series?.source,
                                unit: unitLabel,
                                dateRange: series ? `${series.year_range.start}–${series.year_range.end}` : null,
                                points: chartData.length,
                                note: 'Annual observations from the local dataset; gaps are real reporting gaps, not interpolated.',
                            }}
                        />

                        <ScrollableDataTable
                            rows={chartData}
                            columns={[
                                { key: 'year', label: 'Year' },
                                ...drawnRegions.map(r => ({ key: r, label: r, numeric: true })),
                            ]}
                            filename={`foodberg_geo_${mode}_${(selectedKey || '').replace(/\W+/g, '_')}`}
                        />
                    </>
                ) : (
                    <div className="h-[500px] flex items-center justify-center text-ark-fg-dim">
                        <div className="text-center">
                            <Globe className="w-16 h-16 mx-auto mb-4 text-ark-fg-dim" />
                            <p>No data drawn — select at least one region with data.</p>
                        </div>
                    </div>
                )}
            </div>

            {chartData.length > 0 && drawnRegions.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                    {drawnRegions.map((region) => {
                        const regionData = chartData.filter((d) => d[region] !== undefined)
                        const latest = regionData.length ? regionData[regionData.length - 1] : null
                        const first = regionData.length ? regionData[0] : null
                        const change = first && latest && (first[region] as number)
                            ? (((latest[region] as number) - (first[region] as number)) / (first[region] as number) * 100)
                            : null

                        return (
                            <div
                                key={region}
                                className="card"
                                style={{ borderLeftColor: COLORS[selectedRegions.indexOf(region) % COLORS.length], borderLeftWidth: '4px' }}
                            >
                                <h3 className="font-semibold text-ark-fg capitalize">{region.toLowerCase()}</h3>
                                <div className="text-2xl font-bold text-ark-fg mt-2">
                                    {latest ? (latest[region] as number).toLocaleString(undefined, { maximumFractionDigits: 2 }) : 'N/A'}
                                </div>
                                <div className="text-xs text-ark-fg-dim mt-1">
                                    {latest ? `latest (${latest.year}) · ${unitLabel}` : ''}
                                </div>
                                {change !== null && (
                                    <div className={`text-sm mt-1 ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                        {change >= 0 ? '+' : ''}{change.toFixed(1)}% since {first?.year}
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
