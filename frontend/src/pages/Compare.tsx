import { GitCompareArrows, Search, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import {
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis,
} from 'recharts'
import { useSearchParams } from 'react-router-dom'
import ArkDownloads from '../arcanum/ArkDownloads'
import { useArkTheme } from '../arcanum/arkChartTheme'
import {
    applyTransform,
    clipToRange,
    fmtPrice,
    FREQUENCY_LABEL,
    logSafe,
    normalizeFrequency,
    RANGES,
    TRANSFORMS,
    transformedUnit,
    type Frequency,
    type Obs,
    type RangeKey,
    type TransformKind,
} from '../arcanum/arkTransforms'
import { ScrollableDataTable } from '../components/ChartDetails'
import FreqBadge from '../components/FreqBadge'
import { api } from '../services/api'

// -----------------------------------------------------------------------------
// COMPARE  (route: /compare)
//
// Pin up to six series across items and sources and put them on ONE chart —
// never two charts side by side (WEBSITE_VISUALIZATION_STANDARD).
//
// The defect this page exists to NOT repeat is S3, live on the Food Price Index
// page: `fao_overall` (base 2014-2016 = 100, ~124.5) is plotted against
// `bls_overall` (base 1982-1984 = 100, ~348.0) with reindex OFF by default, so
// the chart appears to say US food costs about three times what world food
// costs. It says no such thing; the two lines simply count from different
// zeros. Two series with different units or different bases share a raw level
// axis ONLY when they are genuinely commensurable. When they are not, this page
// forces the reindex transform on and says so in a visible notice — the reader
// is never left to infer a comparison the axis cannot support.
// -----------------------------------------------------------------------------

// Three BLS Average Price items, all in $ per lb, all live to 2026-06 — so the
// default view is a genuine level comparison rather than a demonstration of the
// mixed-unit guard. A real chart renders on load.
const DEFAULT_SERIES = ['tomatoes-field-grown:retail', 'lettuce-iceberg:retail', 'bananas:retail']

const MAX_PINNED = 6

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

interface Option {
    key: string           // "<slug>:<source>"
    slug: string
    source: SourceKey
    label: string         // human name of the item
    freq: Frequency
    points: number
    span: string
    unit?: string
    liveness?: Liveness
}

interface Loaded {
    key: string
    label: string
    unit: string
    rows: Obs[]
    error?: string
}

const parseKeys = (raw: string | null): string[] => {
    if (!raw) return DEFAULT_SERIES
    const keys = raw.split(',').map(s => s.trim()).filter(Boolean).slice(0, MAX_PINNED)
    return keys.length ? keys : DEFAULT_SERIES
}

export default function Compare() {
    const [searchParams, setSearchParams] = useSearchParams()
    const [coverage, setCoverage] = useState<Record<string, Coverage>>({})
    const [displayNames, setDisplayNames] = useState<Record<string, string>>({})
    const [loaded, setLoaded] = useState<Record<string, Loaded>>({})
    const [filter, setFilter] = useState('')
    const t = useArkTheme()

    // Every piece of state round-trips through the URL, so a comparison is a
    // link someone can send.
    const pinned = useMemo(() => parseKeys(searchParams.get('series')), [searchParams])
    const transform = (searchParams.get('transform') || 'none') as TransformKind
    const range = (searchParams.get('range') || 'max') as RangeKey

    const patch = (next: Partial<{ series: string[]; transform: TransformKind; range: RangeKey }>) => {
        const params: Record<string, string> = {
            series: (next.series ?? pinned).join(','),
            transform: next.transform ?? transform,
            range: next.range ?? range,
        }
        setSearchParams(params, { replace: false })
    }

    useEffect(() => {
        api.getPriceCoverage()
            .then((r) => {
                setCoverage(r.data.commodities || {})
                setDisplayNames(r.data.display_names || {})
            })
            .catch((e) => console.error('Failed to load coverage:', e))
    }, [])

    // Load any pinned series not already in hand. Loads are additive and cached
    // by key, so unpinning and re-pinning does not re-hit the API.
    //
    // `inflight` matters: this effect depends on `loaded`, so every series that
    // resolves re-runs it. Without an in-flight set, three default series would
    // each fire again for every sibling that finished first.
    //
    // And there is deliberately NO per-run `cancelled` flag. The obvious version
    // of that pattern is silently wrong here: this effect re-runs whenever ANY
    // series resolves, so a sibling request created in the previous run would
    // find `cancelled === true`, drop its result, and — having already left the
    // in-flight set — never be retried. The series would simply never appear.
    // Loads are keyed and idempotent, so letting a late response land is right.
    const inflight = useRef<Set<string>>(new Set())
    useEffect(() => {
        for (const key of pinned) {
            if (loaded[key] || inflight.current.has(key)) continue
            const [slug, src] = key.split(':')
            if (!slug || !src) continue
            inflight.current.add(key)
            const request = src === 'av'
                ? api.getPriceHistory(slug)
                : api.getSourceHistory(slug, src)
            request
                .then((r) => {
                    inflight.current.delete(key)
                    const p = r.data
                    const rows: Obs[] = (p.data || []).map((row: { date: string; year: number; price: number }) => ({
                        date: String(row.date).slice(0, 10),
                        year: row.year,
                        price: row.price,
                    }))
                    setLoaded(prev => ({
                        ...prev,
                        [key]: {
                            key,
                            label: p.label || p.source || key,
                            unit: p.unit || 'Unknown unit',
                            rows,
                            error: rows.length ? undefined : (p.note || 'No series in this source.'),
                        },
                    }))
                })
                .catch(() => {
                    inflight.current.delete(key)
                    setLoaded(prev => ({
                        ...prev,
                        [key]: { key, label: key, unit: '', rows: [], error: 'Could not load this series.' },
                    }))
                })
        }
    }, [pinned, loaded])

    // Everything pinnable: a series needs at least two distinct years to be a
    // time series at all (the multi-year honesty gate the Price Explorer
    // already enforces — a single 2025 WASDE value is not a line).
    const options = useMemo<Option[]>(() => {
        const out: Option[] = []
        for (const [slug, cov] of Object.entries(coverage)) {
            for (const s of SOURCE_ORDER) {
                const c = cov[s]
                if (!c) continue
                const multiYear = c.n_years !== undefined ? c.n_years >= 2 : c.points > 1
                if (!multiYear) continue
                out.push({
                    key: `${slug}:${s}`,
                    slug,
                    source: s,
                    label: displayNames[slug] ?? slug,
                    freq: normalizeFrequency(c.frequency),
                    points: c.points,
                    span: `${String(c.start).slice(0, 4)}–${String(c.end).slice(0, 4)}`,
                    unit: c.unit,
                    liveness: c.liveness,
                })
            }
        }
        return out.sort((a, b) => a.label.localeCompare(b.label) || a.source.localeCompare(b.source))
    }, [coverage, displayNames])

    const shown = useMemo(() => {
        const needle = filter.trim().toLowerCase()
        const base = needle
            ? options.filter(o => o.slug.includes(needle) || o.label.toLowerCase().includes(needle))
            : options
        return base.slice(0, 300)
    }, [options, filter])

    const optionFor = (key: string) => options.find(o => o.key === key)

    const toggle = (key: string) => {
        if (pinned.includes(key)) {
            const next = pinned.filter(k => k !== key)
            patch({ series: next.length ? next : DEFAULT_SERIES })
        } else if (pinned.length < MAX_PINNED) {
            patch({ series: [...pinned, key] })
        }
    }

    // ---- THE MIXED-UNIT GUARD ------------------------------------------------
    // Distinct declared units across the pinned set. A single unit means the
    // levels are commensurable and may share a raw axis; more than one means
    // they may not, at any zoom, under any explanation.
    // A stable column/legend name per pinned key. The backend's own `label` is
    // not enough: the Alpha Vantage payload labels itself "Alpha Vantage (global
    // commodity spot prices)" with no commodity in it, so pinning two AV series
    // would produce two identically-named columns in the CSV. Keying the name
    // off `<slug>:<source>` makes it unique by construction.
    const series = useMemo(() => pinned
        .map((k) => {
            const l = loaded[k]
            if (!l || !l.rows.length) return null
            const [slug, src] = k.split(':')
            const itemLabel = displayNames[slug] ?? slug.replace(/-/g, ' ')
            const srcLabel = SOURCE_LABELS[src as SourceKey] ?? src
            return { ...l, colName: `${itemLabel} — ${srcLabel}` }
        })
        .filter((s): s is Loaded & { colName: string } => !!s),
        [pinned, loaded, displayNames])

    const units = useMemo(
        () => Array.from(new Set(series.map(s => s.unit).filter(Boolean))),
        [series],
    )
    const mixedUnits = units.length > 1
    // 'yoy' is already a percent, so it is commensurable regardless of unit.
    // 'none' and 'log' both plot levels, so both are refused when units differ.
    const forcedReindex = mixedUnits && (transform === 'none' || transform === 'log')
    const effective: TransformKind = forcedReindex ? 'reindex' : transform

    // Common rebase date: the earliest date at which EVERY pinned series has an
    // observation. Reindexing each line at its own first observation would put
    // 1980 and 1995 starts on the same 100 and compare nothing; clipping to the
    // shared start makes "=100" mean one date for every line.
    const clipped = useMemo(
        () => series.map(s => ({ ...s, rows: clipToRange(s.rows, range) })),
        [series, range],
    )
    const commonBase = useMemo(() => {
        const firsts = clipped.map(s => s.rows[0]?.date).filter(Boolean) as string[]
        return firsts.length === clipped.length && firsts.length > 0
            ? firsts.reduce((a, b) => (b > a ? b : a))
            : null
    }, [clipped])

    const prepared = useMemo(() => clipped.map((s, i) => {
        let rows = s.rows
        if (effective === 'reindex' && commonBase) rows = rows.filter(r => r.date >= commonBase)
        if (effective === 'log') rows = logSafe(rows).rows
        return {
            ...s,
            id: `s${i}`,
            color: t.colorway[i % t.colorway.length],
            rows: applyTransform(rows, effective),
            droppedForLog: effective === 'log' ? logSafe(s.rows).dropped : 0,
        }
    }), [clipped, effective, commonBase, t.colorway])

    // One row per date across every pinned series; a series with no observation
    // on a date carries no key for it, so recharts leaves a gap rather than
    // interpolating a price nobody published.
    const chartRows = useMemo(() => {
        const byT = new Map<number, Record<string, number>>()
        for (const s of prepared) {
            for (const r of s.rows) {
                const ts = Date.parse(`${r.date}T00:00:00Z`)
                if (!Number.isFinite(ts)) continue
                const row = byT.get(ts) ?? { t: ts }
                row[s.id] = r.price
                byT.set(ts, row)
            }
        }
        return Array.from(byT.values()).sort((a, b) => a.t - b.t)
    }, [prepared])

    // The CSV carries human column names, not the internal s0..s5 chart keys.
    const csvRows = useMemo(() => chartRows.map(r => {
        const out: Record<string, unknown> = {
            date: new Date(r.t).toISOString().slice(0, 10),
        }
        for (const s of prepared) out[s.colName] = r[s.id] ?? ''
        return out
    }), [chartRows, prepared])

    const axisUnit = transformedUnit(effective, mixedUnits ? 'Mixed units — see notice' : (units[0] ?? 'Value'))
    const logDropped = prepared.reduce((n, s) => n + s.droppedForLog, 0)

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-ark-fg mb-2 flex items-center">
                    <GitCompareArrows className="w-8 h-8 mr-3 text-emerald-400" />
                    Compare
                </h1>
                <p className="text-ark-fg-dim">
                    Put up to six price series on one chart — across items, across sources, across the retail
                    and wholesale sides of the same commodity. Every line keeps its own publisher, its own
                    frequency and its own last real observation, all shown beside it.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* PICKER */}
                <div className="lg:col-span-1">
                    <div className="card">
                        <h2 className="text-lg font-semibold text-ark-fg mb-1">
                            Pinned ({pinned.length}/{MAX_PINNED})
                        </h2>
                        <div className="flex flex-wrap gap-2 mb-4">
                            {pinned.map((k, i) => {
                                const o = optionFor(k)
                                const l = loaded[k]
                                return (
                                    <button
                                        key={k}
                                        type="button"
                                        onClick={() => toggle(k)}
                                        className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-ark-tag text-ark-fg hover:bg-ark-line"
                                        title="Remove from the comparison"
                                    >
                                        <span
                                            className="w-2 h-2 rounded-full shrink-0"
                                            style={{ background: t.colorway[i % t.colorway.length] }}
                                        />
                                        {o?.label ?? l?.label ?? k}
                                        <X className="w-3 h-3" />
                                    </button>
                                )
                            })}
                        </div>

                        <div className="relative mb-3">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ark-fg-dim" />
                            <input
                                type="text"
                                placeholder="Add a series — try “tomato”, “beef”, “wheat”…"
                                value={filter}
                                onChange={(e) => setFilter(e.target.value)}
                                className="w-full pl-9 pr-3 py-2 bg-ark-tag border border-ark-line rounded-lg text-ark-fg placeholder-ark-fg-dim focus:outline-none focus:border-emerald-500 text-sm"
                            />
                        </div>

                        <div className="space-y-1 max-h-[520px] overflow-y-auto">
                            {shown.length === 0 && (
                                <p className="text-sm text-ark-fg-dim py-3">
                                    {options.length === 0
                                        ? 'Loading the catalog…'
                                        : `Nothing matches “${filter.trim()}”.`}
                                </p>
                            )}
                            {shown.map(o => {
                                const on = pinned.includes(o.key)
                                const full = !on && pinned.length >= MAX_PINNED
                                return (
                                    <button
                                        key={o.key}
                                        type="button"
                                        disabled={full}
                                        onClick={() => toggle(o.key)}
                                        className={`w-full text-left p-2 rounded-lg transition-colors ${on
                                            ? 'bg-emerald-600/20 border border-emerald-500/50'
                                            : full
                                                ? 'opacity-40 cursor-default border border-transparent'
                                                : 'bg-ark-bg-soft hover:bg-ark-tag border border-transparent'
                                            }`}
                                    >
                                        <div className="flex justify-between items-center gap-2">
                                            <span className="text-sm font-medium text-ark-fg">{o.label}</span>
                                            {/* Shared badge: this used to paint EVERY frequency
                                                emerald, which made an annual series look like
                                                the recommended one on the page whose whole
                                                point is that annual is too coarse. */}
                                            <FreqBadge freq={o.freq} />
                                        </div>
                                        <div className="text-xs text-ark-fg-dim">
                                            {SOURCE_LABELS[o.source]} · {o.span}
                                            {o.unit ? ` · ${o.unit}` : ''}
                                        </div>
                                    </button>
                                )
                            })}
                        </div>
                        {pinned.length >= MAX_PINNED && (
                            <p className="text-xs text-ark-fg-dim mt-3">
                                Six lines is the limit — beyond that a reader cannot tell them apart. Unpin one
                                to add another.
                            </p>
                        )}
                    </div>
                </div>

                {/* CHART */}
                <div className="lg:col-span-2">
                    <div className="card">
                        <div className="flex justify-between items-start gap-3 flex-wrap mb-3">
                            <h2 className="text-xl font-semibold text-ark-fg">
                                {prepared.length} series compared
                            </h2>
                            {/* Universal Graph Contract: the download sits top-right of
                                the chart it belongs to, and carries exactly the rows
                                that were plotted — transform included. */}
                            <ArkDownloads
                                rows={csvRows}
                                filename={`foodberg_comparison_${effective}_${range}`}
                                label={null}
                            />
                        </div>

                        {/* CONTROLS — always visible, never behind an "advanced" disclosure. */}
                        <div className="flex flex-wrap gap-2 mb-3">
                            {TRANSFORMS.map(tr => (
                                <button
                                    key={tr.key}
                                    type="button"
                                    title={tr.hint}
                                    onClick={() => patch({ transform: tr.key })}
                                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${transform === tr.key
                                        ? 'bg-emerald-600 text-white'
                                        : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                        }`}
                                >
                                    {tr.label}
                                </button>
                            ))}
                        </div>
                        <div className="flex flex-wrap gap-2 mb-4">
                            {RANGES.map(r => (
                                <button
                                    key={r.key}
                                    type="button"
                                    onClick={() => patch({ range: r.key })}
                                    className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${range === r.key
                                        ? 'bg-emerald-600 text-white'
                                        : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                        }`}
                                >
                                    {r.label}
                                </button>
                            ))}
                        </div>

                        {/* The S3 guard, stated out loud. */}
                        {forcedReindex && (
                            <div className="mb-4 px-3 py-2 rounded-lg border border-amber-500/50 bg-amber-50 text-sm text-amber-900 dark:bg-amber-900/20 dark:text-amber-200">
                                <strong>These series are not in the same unit</strong> ({units.join(' · ')}), so
                                their raw levels cannot share an axis — a line at 350 would not be “higher
                                priced” than a line at 124, it would just be counting from a different zero.
                                The chart is showing <strong>Reindex (=100)</strong> instead. Pick “YoY change
                                %”, or pin series that share a unit, to see something other than an index.
                            </div>
                        )}
                        {effective === 'reindex' && commonBase && (
                            <p className="text-xs text-ark-fg-dim mb-3">
                                Every line = 100 at {commonBase.slice(0, 7)} — the earliest month all pinned
                                series share. Observations before that date are not plotted, so the base is one
                                date rather than a different date per line.
                            </p>
                        )}
                        {effective === 'log' && logDropped > 0 && (
                            <p className="text-xs text-ark-fg-dim mb-3">
                                {logDropped} observation{logDropped === 1 ? '' : 's'} at or below zero cannot be
                                placed on a log axis and {logDropped === 1 ? 'is' : 'are'} not plotted.
                            </p>
                        )}

                        {chartRows.length === 0 ? (
                            <div className="h-[380px] flex items-center justify-center text-ark-fg-dim">
                                {pinned.some(k => !loaded[k]) ? 'Loading the pinned series…' : 'Nothing to plot.'}
                            </div>
                        ) : (
                            <div className="h-[420px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={chartRows} margin={{ left: 12, bottom: 8 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke={t.gridStroke} />
                                        <XAxis
                                            dataKey="t"
                                            type="number"
                                            scale="time"
                                            domain={['dataMin', 'dataMax']}
                                            stroke={t.axisStroke}
                                            tick={{ fill: t.dim }}
                                            tickFormatter={(v: number) => String(new Date(v).getUTCFullYear())}
                                        />
                                        <YAxis
                                            stroke={t.axisStroke}
                                            tick={{ fill: t.dim }}
                                            scale={effective === 'log' ? 'log' : 'auto'}
                                            domain={effective === 'log' ? ['auto', 'auto'] : undefined}
                                            tickFormatter={(v: number) => v.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                                            label={{ value: axisUnit, angle: -90, position: 'insideLeft', fill: t.dim, fontSize: 12 }}
                                        />
                                        <Tooltip
                                            contentStyle={t.tooltip}
                                            labelStyle={{ color: t.fg }}
                                            labelFormatter={(v: number) => new Date(v).toISOString().slice(0, 10)}
                                            formatter={(value: number, name: string) => [
                                                fmtPrice(value, effective === 'none' ? axisUnit : undefined),
                                                name,
                                            ]}
                                        />
                                        {prepared.map(s => (
                                            <Line
                                                key={s.id}
                                                type="monotone"
                                                dataKey={s.id}
                                                name={s.colName}
                                                stroke={s.color}
                                                strokeWidth={2}
                                                dot={false}
                                                connectNulls={false}
                                                isAnimationActive={false}
                                            />
                                        ))}
                                        {/* Legend BELOW the chart — WEBSITE_VISUALIZATION_STANDARD. */}
                                        <Legend
                                            verticalAlign="bottom"
                                            align="center"
                                            wrapperStyle={{ paddingTop: 12, color: t.dim, fontSize: 12 }}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        )}

                        {/* PER-SERIES PROVENANCE — publisher, frequency, unit, and the
                            last REAL observation. A series that a publisher quietly
                            stopped updating is labelled here, not left to look current
                            because its line reaches the right-hand edge. */}
                        <div className="mt-6 pt-4 border-t border-ark-line">
                            <h3 className="text-sm font-semibold text-ark-fg-dim uppercase tracking-wide mb-3">
                                What each line is
                            </h3>
                            <div className="space-y-3">
                                {pinned.map((k, i) => {
                                    const o = optionFor(k)
                                    const l = loaded[k]
                                    const live = o?.liveness
                                    return (
                                        <div key={k} className="flex items-start gap-2 text-sm">
                                            <span
                                                className="w-3 h-3 rounded-full shrink-0 mt-1"
                                                style={{ background: t.colorway[i % t.colorway.length] }}
                                            />
                                            <div>
                                                <div className="text-ark-fg font-medium">
                                                    {l?.label ?? o?.label ?? k}
                                                </div>
                                                <div className="text-xs text-ark-fg-dim">
                                                    {o ? `${SOURCE_LABELS[o.source]} · ${FREQUENCY_LABEL[o.freq]}` : k}
                                                    {l?.unit ? ` · ${l.unit}` : ''}
                                                    {l?.rows.length ? ` · ${l.rows.length.toLocaleString()} observations` : ''}
                                                    {live?.last_real_observation
                                                        ? ` · last real observation ${live.last_real_observation.slice(0, 7)}`
                                                        : ''}
                                                </div>
                                                {live && live.status !== 'live' && (
                                                    <div className="text-xs text-amber-700 dark:text-amber-300 mt-0.5">
                                                        {live.status === 'discontinued' ? 'Discontinued' : 'Stale'}
                                                        {live.months_behind != null ? ` — ${live.months_behind} months behind the rest of this source` : ''}
                                                        . The history is real; the series is not current.
                                                    </div>
                                                )}
                                                {l?.error && (
                                                    <div className="text-xs text-amber-700 dark:text-amber-300 mt-0.5">{l.error}</div>
                                                )}
                                                {!l && (
                                                    <div className="text-xs text-ark-fg-dim mt-0.5">Loading…</div>
                                                )}
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>

                        <ScrollableDataTable
                            title="Plotted data"
                            rows={csvRows}
                            columns={[
                                { key: 'date', label: 'Date' },
                                ...prepared.map(s => ({ key: s.colName, label: s.colName, numeric: true })),
                            ]}
                            filename={`foodberg_comparison_${effective}_${range}`}
                        />
                    </div>
                </div>
            </div>
        </div>
    )
}
