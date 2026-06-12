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
import { useArkTheme } from '../arcanum/arkChartTheme'
import { ChartMetaStrip, ScrollableDataTable } from '../components/ChartDetails'

// Color palette for multiple lines
const COLORS = [
    '#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
]

interface GeoIndicator {
    indicator_code: string
    name: string
    unit: string | null
    n_regions: number
    year_start: number
    year_end: number
    n_obs: number
}

interface GeoSeries {
    indicator_code: string
    name: string
    unit: string | null
    regions: string[]
    n_obs: number
    year_range: { start: number; end: number }
    data: Array<{ region: string; year: number; value: number }>
    source: string
}

/* Geographic comparison over the REAL multi-country data in the local
   dataset: World Bank agriculture/food indicators, annual, 1990-2024, for
   nine named regions. (The per-commodity price series are global composites
   with no per-country breakdown, so commodity prices cannot honestly be
   compared across countries here.) */
export default function GeographicPrices() {
    const [indicators, setIndicators] = useState<GeoIndicator[]>([])
    const [selectedIndicator, setSelectedIndicator] = useState<string | null>(null)
    const [series, setSeries] = useState<GeoSeries | null>(null)
    const [selectedRegions, setSelectedRegions] = useState<string[]>(['United States', 'China', 'Brazil'])
    const [loading, setLoading] = useState(true)
    const t = useArkTheme()

    useEffect(() => {
        api.getGeoIndicators()
            .then((res) => {
                const list: GeoIndicator[] = res.data.indicators || []
                setIndicators(list)
                if (list.length) setSelectedIndicator(list[0].indicator_code)
            })
            .catch((e) => console.error('Failed to load indicators:', e))
            .finally(() => setLoading(false))
    }, [])

    useEffect(() => {
        if (!selectedIndicator) return
        setLoading(true)
        api.getGeoSeries(selectedIndicator)
            .then((res) => setSeries(res.data.status === 'data_unavailable' ? null : res.data))
            .catch((e) => console.error('Failed to load series:', e))
            .finally(() => setLoading(false))
    }, [selectedIndicator])

    const toggleRegion = (region: string) => {
        if (selectedRegions.includes(region)) {
            setSelectedRegions(selectedRegions.filter(r => r !== region))
        } else if (selectedRegions.length < 6) {
            setSelectedRegions([...selectedRegions, region])
        }
    }

    // Regions that actually have rows for this indicator.
    const regionsWithData = new Set(series?.regions ?? [])
    const drawnRegions = selectedRegions.filter(r => regionsWithData.has(r))
    const missingRegions = selectedRegions.filter(r => !regionsWithData.has(r))

    // Pivot rows -> one object per year with a key per drawn region.
    const chartData = (() => {
        if (!series) return []
        const byYear: Record<number, any> = {}
        for (const row of series.data) {
            if (!drawnRegions.includes(row.region)) continue
            byYear[row.year] ||= { year: row.year }
            byYear[row.year][row.region] = row.value
        }
        return Object.values(byYear).sort((a: any, b: any) => a.year - b.year)
    })()

    const current = indicators.find(i => i.indicator_code === selectedIndicator)
    const unitLabel = series?.unit || current?.unit || 'Value'

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-ark-fg mb-2 flex items-center">
                    <Globe className="w-8 h-8 mr-3 text-blue-400" />
                    Geographic Comparison
                </h1>
                <p className="text-ark-fg-dim">
                    Compare countries on World Bank agriculture and food indicators — annual data,
                    1990–2024, from the local dataset. (Per-commodity spot prices are global
                    composites with no per-country breakdown, so they are not shown here.)
                </p>
            </div>

            <div className="card mb-6">
                <h2 className="text-lg font-semibold text-ark-fg mb-4">Select Indicator</h2>
                <div className="flex flex-wrap gap-2">
                    {indicators.map(ind => (
                        <button
                            key={ind.indicator_code}
                            onClick={() => setSelectedIndicator(ind.indicator_code)}
                            title={`${ind.year_start}–${ind.year_end} · ${ind.n_regions} regions`}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors text-sm ${selectedIndicator === ind.indicator_code
                                ? 'bg-emerald-600 text-white'
                                : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                }`}
                        >
                            {ind.name}
                        </button>
                    ))}
                </div>
            </div>

            <div className="card mb-6">
                <h2 className="text-lg font-semibold text-ark-fg mb-4">
                    Select Regions to Compare (max 6)
                    <span className="text-sm text-ark-fg-dim ml-2">
                        ({drawnRegions.length} drawn{missingRegions.length ? `, ${missingRegions.length} without data` : ''})
                    </span>
                </h2>

                {series ? (
                    <>
                        <div className="flex flex-wrap gap-2">
                            {series.regions.map((region) => (
                                <button
                                    key={region}
                                    onClick={() => toggleRegion(region)}
                                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center ${selectedRegions.includes(region)
                                        ? 'text-white'
                                        : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                        }`}
                                    style={selectedRegions.includes(region) ? {
                                        backgroundColor: COLORS[selectedRegions.indexOf(region) % COLORS.length]
                                    } : {}}
                                    disabled={!selectedRegions.includes(region) && selectedRegions.length >= 6}
                                >
                                    <MapPin className="w-3 h-3 mr-1" />
                                    {region}
                                </button>
                            ))}
                        </div>
                        {missingRegions.length > 0 && (
                            <p className="text-xs text-amber-400/80 mt-3">
                                No data for this indicator: {missingRegions.join(', ')} — deselect or pick another indicator.
                            </p>
                        )}
                    </>
                ) : (
                    <p className="text-ark-fg-dim">Loading available regions...</p>
                )}
            </div>

            <div className="card">
                <h2 className="text-xl font-semibold text-ark-fg mb-4">
                    {series?.name || 'Indicator'} by Region
                </h2>

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
                                note: 'Annual World Bank observations from the local dataset; gaps are real reporting gaps, not interpolated.',
                            }}
                        />

                        <ScrollableDataTable
                            rows={chartData}
                            columns={[
                                { key: 'year', label: 'Year' },
                                ...drawnRegions.map(r => ({ key: r, label: r, numeric: true })),
                            ]}
                            filename={`foodberg_geo_${selectedIndicator}`}
                        />
                    </>
                ) : (
                    <div className="h-[500px] flex items-center justify-center text-ark-fg-dim">
                        <div className="text-center">
                            <Globe className="w-16 h-16 mx-auto mb-4 text-ark-fg-dim" />
                            <p>No data drawn — select at least one region with data for this indicator.</p>
                        </div>
                    </div>
                )}
            </div>

            {chartData.length > 0 && drawnRegions.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                    {drawnRegions.map((region) => {
                        const regionData = chartData.filter((d: any) => d[region] !== undefined)
                        const latest = regionData.length ? regionData[regionData.length - 1] : null
                        const first = regionData.length ? regionData[0] : null
                        const change = first && latest && first[region]
                            ? ((latest[region] - first[region]) / first[region] * 100)
                            : null

                        return (
                            <div
                                key={region}
                                className="card"
                                style={{ borderLeftColor: COLORS[selectedRegions.indexOf(region) % COLORS.length], borderLeftWidth: '4px' }}
                            >
                                <h3 className="font-semibold text-ark-fg">{region}</h3>
                                <div className="text-2xl font-bold text-ark-fg mt-2">
                                    {latest ? latest[region].toLocaleString(undefined, { maximumFractionDigits: 2 }) : 'N/A'}
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
