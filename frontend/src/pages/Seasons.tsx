import { CalendarRange, Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
    Area,
    CartesianGrid,
    ComposedChart,
    Legend,
    Line,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis,
} from 'recharts'
import { useArkTheme } from '../arcanum/arkChartTheme'
import {
    fmtPct,
    fmtPrice,
    hasSeasonalSignal,
    normalizeFrequency,
    seasonality,
    type Frequency,
    type Obs,
    type Seasonality,
} from '../arcanum/arkTransforms'
import { ChartMetaStrip, ScrollableDataTable } from '../components/ChartDetails'
import { api } from '../services/api'

// -----------------------------------------------------------------------------
// SEASONS  (route: /seasons)  —  "when is a tomato cheap"
//
// This is the chef's question, and the answer has been sitting in the database
// the whole time being thrown away. The Price Explorer charted monthly series
// with `dataKey="year"`, and Historical Trends says outright that "monthly
// series are averaged into annual points" — both collapse the month-of-year
// signal, which is precisely the signal a kitchen buys on.
//
// Nothing is computed here that arkTransforms does not compute: `seasonality()`
// owns the window, the per-month quantiles, the cheapest/dearest months, the
// swing and the current percentile. This page selects a series, hands it over,
// and renders the result honestly — including refusing to draw anything when
// the series is too thin for a month-of-year profile to mean anything.
// -----------------------------------------------------------------------------

// The canonical default: BLS AP series APU0000712311, "Tomatoes, field grown",
// 552 monthly observations 1980-01 → 2026-06 in $ per lb. A real price renders
// on load — never an empty state, never "select a commodity to begin".
const DEFAULT_ITEM = 'tomatoes-field-grown'
const DEFAULT_SOURCE = 'retail'

// A month-of-year profile needs monthly-or-finer data AND enough of it.
// seasonality() itself refuses below 24 dated observations; the picker refuses
// earlier so a chef is never offered an item that cannot answer the question.
const MIN_OBS_FOR_PICKER = 24

interface Liveness {
    status: 'live' | 'stale' | 'discontinued' | 'unknown'
    months_behind: number | null
    last_real_observation: string | null
}

interface SourceCov {
    points: number
    frequency: string
    start: string
    end: string
    label?: string
    n_years?: number
    unit?: string
    liveness?: Liveness
}

type SourceKey = 'av' | 'nass' | 'pinksheet' | 'retail'
type Coverage = Partial<Record<SourceKey, SourceCov>>

const SOURCE_ORDER: SourceKey[] = ['retail', 'pinksheet', 'av', 'nass']

const SOURCE_LABELS: Record<SourceKey, string> = {
    nass: 'US farm gate (USDA)',
    av: 'Global spot (monthly)',
    pinksheet: 'Global spot (Pink Sheet)',
    retail: 'US retail (BLS)',
}

interface Candidate {
    slug: string
    label: string
    source: SourceKey
    freq: Frequency
    points: number
    span: string
    liveness?: Liveness
}

interface Series {
    label: string
    unit: string
    rows: Obs[]
    dataPoints: number
    dateRange: string | null
    note?: string
    hasHistory: boolean
}

export default function Seasons() {
    const [searchParams, setSearchParams] = useSearchParams()
    const [coverage, setCoverage] = useState<Record<string, Coverage>>({})
    const [displayNames, setDisplayNames] = useState<Record<string, string>>({})
    const [series, setSeries] = useState<Series | null>(null)
    const [seriesError, setSeriesError] = useState<string | null>(null)
    const [filter, setFilter] = useState('')
    const t = useArkTheme()

    // Every piece of page state round-trips through the URL, so a chef can send
    // "here is when lettuce is cheap" as a link.
    const item = (searchParams.get('item') || DEFAULT_ITEM).toLowerCase()
    const source = (searchParams.get('source') || DEFAULT_SOURCE) as SourceKey

    const select = (nextItem: string, nextSource: SourceKey) => {
        setSearchParams({ item: nextItem, source: nextSource }, { replace: false })
    }

    useEffect(() => {
        api.getPriceCoverage()
            .then((r) => {
                setCoverage(r.data.commodities || {})
                setDisplayNames(r.data.display_names || {})
            })
            .catch((e) => console.error('Failed to load coverage:', e))
    }, [])

    // The series load does NOT wait on coverage: the default item is known, so
    // the chart is on its way before the picker has finished populating.
    useEffect(() => {
        let cancelled = false
        setSeries(null)
        setSeriesError(null)
        const request = source === 'av'
            ? api.getPriceHistory(item)
            : api.getSourceHistory(item, source)
        request
            .then((r) => {
                if (cancelled) return
                const p = r.data
                const rows: Obs[] = (p.data || []).map((row: { date: string; year: number; price: number }) => ({
                    date: String(row.date).slice(0, 10),
                    year: row.year,
                    price: row.price,
                }))
                setSeries({
                    label: p.label || p.source || `${item} (${source})`,
                    unit: p.unit || 'Unknown unit',
                    rows,
                    dataPoints: p.data_points ?? rows.length,
                    dateRange: p.date_range ? `${p.date_range.start} → ${p.date_range.end}` : null,
                    note: p.note,
                    hasHistory: !!p.has_history,
                })
            })
            .catch((e) => {
                console.error('Failed to load series:', e)
                if (!cancelled) setSeriesError('Could not load this series. The data API may be offline.')
            })
        return () => { cancelled = true }
    }, [item, source])

    // Only monthly-or-finer sources can carry a month-of-year signal. NASS
    // reports its frequency as "annual+monthly"; normalizeFrequency resolves
    // that to `annual`, because what the explorer can actually chart from it is
    // the annual series — calling it monthly would smuggle an annual series past
    // this filter and produce a "seasonal profile" with one month in it.
    const candidates = useMemo<Candidate[]>(() => {
        const out: Candidate[] = []
        for (const [slug, cov] of Object.entries(coverage)) {
            const usable = SOURCE_ORDER
                .map((s) => ({ s, c: cov[s] }))
                .filter((x): x is { s: SourceKey; c: SourceCov } => {
                    if (!x.c) return false
                    if (!hasSeasonalSignal(normalizeFrequency(x.c.frequency))) return false
                    return x.c.points >= MIN_OBS_FOR_PICKER
                })
            if (!usable.length) continue
            // One row per commodity, using its richest seasonal source; the
            // other sources appear as tabs once the commodity is selected.
            const best = usable.reduce((a, b) => (b.c.points > a.c.points ? b : a), usable[0])
            out.push({
                slug,
                label: displayNames[slug] ?? slug,
                source: best.s,
                freq: normalizeFrequency(best.c.frequency),
                points: best.c.points,
                span: `${String(best.c.start).slice(0, 4)}–${String(best.c.end).slice(0, 4)}`,
                liveness: best.c.liveness,
            })
        }
        return out.sort((a, b) => a.label.localeCompare(b.label))
    }, [coverage, displayNames])

    const shown = useMemo(() => {
        const needle = filter.trim().toLowerCase()
        if (!needle) return candidates
        return candidates.filter(c => c.slug.includes(needle) || c.label.toLowerCase().includes(needle))
    }, [candidates, filter])

    // Which other sources can answer the seasonal question for THIS item.
    const itemSources = useMemo<SourceKey[]>(() => {
        const cov = coverage[item] ?? {}
        return SOURCE_ORDER.filter((s) => {
            const c = cov[s]
            return !!c && hasSeasonalSignal(normalizeFrequency(c.frequency)) && c.points >= MIN_OBS_FOR_PICKER
        })
    }, [coverage, item])

    const season: Seasonality | null = useMemo(
        () => (series?.rows.length ? seasonality(series.rows) : null),
        [series],
    )

    const title = displayNames[item] ?? item.replace(/-/g, ' ')
    const unit = series?.unit ?? ''

    // One row per reported month. `band` is a two-element range, which is how
    // recharts draws a filled p25–p75 envelope; `latestYear` is the most recent
    // year's own months, left undefined (not zero-filled) for months that year
    // has not reached.
    const chartRows = useMemo(() => (season?.months ?? []).map(m => ({
        name: m.name,
        band: [m.p25, m.p75] as [number, number],
        median: m.median,
        latestYear: m.latestYear,
        n: m.n,
    })), [season])

    const tableRows = useMemo(() => (season?.months ?? []).map(m => ({
        month: m.name,
        years: m.n,
        median: m.median,
        p25: m.p25,
        p75: m.p75,
        min: m.min,
        max: m.max,
        indexed: m.indexed,
        latest_year: m.latestYear ?? null,
    })), [season])

    // Why a series cannot produce a seasonal profile, in words. Never a
    // half-empty chart, never a silent blank.
    const refusal = (): string | null => {
        if (!series) return null
        if (!series.hasHistory || !series.rows.length) {
            return series.note || 'This source carries no series for this item.'
        }
        if (season) return null
        const dated = series.rows.filter(r => r.date.length >= 7).length
        if (dated < 24) {
            return `Only ${dated} observation${dated === 1 ? '' : 's'} in this series carry a month, and a month-of-year profile needs at least 24. There is real history here — it is on the Price Explorer — but there is not enough of it to say when this item is cheap.`
        }
        return 'Fewer than six months of the year have at least three years of observations in the trailing 20-year window, so there is no seasonal profile to draw. A shape built from one or two years per month would look confident and mean nothing.'
    }
    const cannot = refusal()

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-ark-fg mb-2 flex items-center">
                    <CalendarRange className="w-8 h-8 mr-3 text-emerald-400" />
                    Seasons
                </h1>
                <p className="text-ark-fg-dim">
                    When is a tomato cheap? Every monthly series on this site is redrawn against the month of
                    the year rather than the calendar, so the seasonal shape a kitchen buys on becomes visible.
                    The band is the middle half of the observed history — the 25th to the 75th percentile of
                    what that month actually cost — and the line through it is the median. Nothing is smoothed,
                    modelled, or forecast.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* PICKER */}
                <div className="lg:col-span-1">
                    <div className="card">
                        <h2 className="text-lg font-semibold text-ark-fg mb-3">
                            Monthly-or-finer series ({shown.length})
                        </h2>
                        <div className="relative mb-3">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ark-fg-dim" />
                            <input
                                type="text"
                                placeholder="Filter — try “tomato”, “bread”, “coffee”…"
                                value={filter}
                                onChange={(e) => setFilter(e.target.value)}
                                className="w-full pl-9 pr-3 py-2 bg-ark-tag border border-ark-line rounded-lg text-ark-fg placeholder-ark-fg-dim focus:outline-none focus:border-emerald-500 text-sm"
                            />
                        </div>
                        <p className="text-xs text-ark-fg-dim mb-3">
                            Annual sources are absent by design: a series with one observation a year cannot say
                            anything about months. That excludes USDA farm-gate prices and FAOSTAT.
                        </p>
                        <div className="space-y-2 max-h-[520px] overflow-y-auto">
                            {shown.length === 0 && (
                                <p className="text-sm text-ark-fg-dim py-3">
                                    {candidates.length === 0
                                        ? 'Loading the catalog…'
                                        : `Nothing monthly matches “${filter.trim()}”.`}
                                </p>
                            )}
                            {shown.map(c => (
                                <button
                                    key={c.slug}
                                    type="button"
                                    onClick={() => select(c.slug, c.source)}
                                    className={`w-full text-left p-3 rounded-lg transition-colors ${item === c.slug
                                        ? 'bg-emerald-600/20 border border-emerald-500/50'
                                        : 'bg-ark-bg-soft hover:bg-ark-tag border border-transparent'
                                        }`}
                                >
                                    <div className="flex justify-between items-center gap-2">
                                        <span className="font-medium text-ark-fg">{c.label}</span>
                                        <span className="shrink-0 text-[10px] font-semibold uppercase tracking-wide text-emerald-400 bg-emerald-900/30 px-1.5 py-0.5 rounded">
                                            {c.freq}
                                        </span>
                                    </div>
                                    <div className="text-xs text-ark-fg-dim mt-1">
                                        {c.span} · {c.points.toLocaleString()} obs · {SOURCE_LABELS[c.source]}
                                    </div>
                                    {c.liveness && c.liveness.status !== 'live' && (
                                        <div className="text-[10px] font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300 mt-1">
                                            {c.liveness.status} — last real value{' '}
                                            {c.liveness.last_real_observation?.slice(0, 7) ?? 'unknown'}
                                        </div>
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* CHART + STATS */}
                <div className="lg:col-span-2">
                    <div className="card">
                        <div className="flex justify-between items-start gap-3 flex-wrap mb-2">
                            <h2 className="text-xl font-semibold text-ark-fg capitalize">
                                {title} — by month of the year
                            </h2>
                        </div>

                        {itemSources.length > 1 && (
                            <div className="flex gap-2 mb-4 flex-wrap">
                                {itemSources.map(s => (
                                    <button
                                        key={s}
                                        type="button"
                                        onClick={() => select(item, s)}
                                        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${source === s
                                            ? 'bg-emerald-600 text-white'
                                            : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                            }`}
                                    >
                                        {SOURCE_LABELS[s]}
                                    </button>
                                ))}
                            </div>
                        )}

                        {seriesError && <div className="text-red-400 py-8">{seriesError}</div>}

                        {!seriesError && !series && (
                            <div className="h-[380px] flex items-center justify-center text-ark-fg-dim">
                                Loading {title}…
                            </div>
                        )}

                        {series && cannot && (
                            <div className="py-8">
                                <div className="text-sm uppercase tracking-wide text-amber-400/80 mb-2">
                                    No seasonal profile for this series
                                </div>
                                <p className="text-ark-fg-dim max-w-2xl">{cannot}</p>
                            </div>
                        )}

                        {series && season && (
                            <>
                                <p className="text-sm text-ark-fg-dim mb-3">
                                    Median of the {season.yearsUsed} years {season.yearFrom}–{season.yearTo}
                                    {season.months.length < 12
                                        ? ` · ${season.months.length} of 12 months have at least three years of observations and are shown; the rest are omitted rather than guessed`
                                        : ''}
                                    .
                                </p>

                                <div className="h-[380px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <ComposedChart data={chartRows} margin={{ left: 12, bottom: 8 }}>
                                            <CartesianGrid strokeDasharray="3 3" stroke={t.gridStroke} />
                                            <XAxis
                                                dataKey="name"
                                                stroke={t.axisStroke}
                                                tick={{ fill: t.dim }}
                                            />
                                            <YAxis
                                                stroke={t.axisStroke}
                                                tick={{ fill: t.dim }}
                                                tickFormatter={(v: number) => v.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                                                label={{ value: unit, angle: -90, position: 'insideLeft', fill: t.dim, fontSize: 12 }}
                                            />
                                            <Tooltip
                                                contentStyle={t.tooltip}
                                                labelStyle={{ color: t.fg }}
                                                formatter={(value: number | number[], name: string) => {
                                                    if (Array.isArray(value)) {
                                                        return [`${fmtPrice(value[0], unit)} – ${fmtPrice(value[1], unit)}`, name]
                                                    }
                                                    return [fmtPrice(value, unit), name]
                                                }}
                                            />
                                            {/* The band is a range series: one filled area between the
                                                25th and 75th percentile of that month's observations. */}
                                            <Area
                                                dataKey="band"
                                                name="Middle half of observed months (25th–75th pct)"
                                                stroke="none"
                                                fill={t.accent}
                                                fillOpacity={0.18}
                                                isAnimationActive={false}
                                            />
                                            <Line
                                                type="monotone"
                                                dataKey="median"
                                                name={`Median, ${season.yearFrom}–${season.yearTo}`}
                                                stroke={t.accent}
                                                strokeWidth={2.5}
                                                dot={{ r: 3, fill: t.accent }}
                                                isAnimationActive={false}
                                            />
                                            <Line
                                                type="monotone"
                                                dataKey="latestYear"
                                                name={`${season.yearTo} so far`}
                                                stroke={t.colorway[2]}
                                                strokeWidth={2}
                                                strokeDasharray="5 3"
                                                dot={{ r: 3, fill: t.colorway[2] }}
                                                connectNulls={false}
                                                isAnimationActive={false}
                                            />
                                            {/* Legend BELOW the chart — WEBSITE_VISUALIZATION_STANDARD. */}
                                            <Legend
                                                verticalAlign="bottom"
                                                align="center"
                                                wrapperStyle={{ paddingTop: 12, color: t.dim, fontSize: 12 }}
                                            />
                                        </ComposedChart>
                                    </ResponsiveContainer>
                                </div>

                                {/* The four answers a kitchen actually wants. Every one of
                                    these is returned by seasonality(); none is recomputed
                                    here, so the chart and the cards can never disagree. */}
                                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
                                    <div className="bg-ark-bg-soft rounded-lg p-3">
                                        <div className="text-xs uppercase tracking-wide text-ark-fg-dim">Cheapest month</div>
                                        <div className="text-2xl font-bold text-emerald-400">
                                            {season.cheapest?.name ?? '—'}
                                        </div>
                                        <div className="text-xs text-ark-fg-dim">
                                            median {fmtPrice(season.cheapest?.median, unit)}
                                        </div>
                                    </div>
                                    <div className="bg-ark-bg-soft rounded-lg p-3">
                                        <div className="text-xs uppercase tracking-wide text-ark-fg-dim">Dearest month</div>
                                        <div className="text-2xl font-bold text-amber-400">
                                            {season.dearest?.name ?? '—'}
                                        </div>
                                        <div className="text-xs text-ark-fg-dim">
                                            median {fmtPrice(season.dearest?.median, unit)}
                                        </div>
                                    </div>
                                    <div className="bg-ark-bg-soft rounded-lg p-3">
                                        <div className="text-xs uppercase tracking-wide text-ark-fg-dim">Seasonal swing</div>
                                        <div className="text-2xl font-bold text-ark-fg">
                                            {fmtPct(season.swingPct)}
                                        </div>
                                        <div className="text-xs text-ark-fg-dim">dearest over cheapest</div>
                                    </div>
                                    <div className="bg-ark-bg-soft rounded-lg p-3">
                                        <div className="text-xs uppercase tracking-wide text-ark-fg-dim">
                                            Latest vs its own month
                                        </div>
                                        <div className="text-2xl font-bold text-ark-fg">
                                            {season.currentPercentile == null
                                                ? '—'
                                                : `${Math.round(season.currentPercentile)}th`}
                                        </div>
                                        <div className="text-xs text-ark-fg-dim">
                                            {season.currentPercentile == null
                                                ? 'too few observations in that month to rank'
                                                : `percentile of every ${season.currentMonth?.name ?? ''} on record`}
                                        </div>
                                    </div>
                                </div>

                                <ChartMetaStrip
                                    meta={{
                                        source: series.label,
                                        unit,
                                        dateRange: series.dateRange,
                                        points: series.dataPoints,
                                        latestLabel: 'Seasonal window',
                                        latestValue: `${season.yearFrom}–${season.yearTo} (${season.yearsUsed} years)`,
                                        note: 'Per-month statistics are computed from the observations themselves over a trailing 20-year window. A month is only reported when at least three years contributed to it.',
                                    }}
                                />

                                <ScrollableDataTable
                                    title="Month-of-year statistics"
                                    rows={tableRows}
                                    columns={[
                                        { key: 'month', label: 'Month' },
                                        { key: 'years', label: 'Years', numeric: true },
                                        { key: 'median', label: `Median (${unit})`, numeric: true },
                                        { key: 'p25', label: '25th pct', numeric: true },
                                        { key: 'p75', label: '75th pct', numeric: true },
                                        { key: 'min', label: 'Lowest', numeric: true },
                                        { key: 'max', label: 'Highest', numeric: true },
                                        { key: 'indexed', label: 'vs all-month median (=100)', numeric: true },
                                        { key: 'latest_year', label: `${season.yearTo}`, numeric: true },
                                    ]}
                                    filename={`foodberg_${item}_${source}_seasonality`}
                                />
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
