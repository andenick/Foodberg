// =============================================================================
// Arcanum Site Kit — arkTransforms.ts (React/TS parity port of ark-chart.js v1.0)
//
// The kit's transform cluster is implemented in `ark-chart.js` as a vanilla-JS
// Plotly wrapper. Foodberg is a React/recharts SPA and cannot load that file, so
// this module is the **contract-faithful port**: the same transform names, the
// same labels, the same "recomputed IN-BROWSER, never server compute" rule
// (WEBSITE_VISUALIZATION_STANDARD §2/§3). Any fix to a transform here should be
// mirrored back into `ark-chart.js` and vice versa.
//
// It adds three things the kit does not have, because they are food-price
// specific and are the chef features this site exists to serve:
//
//   REAL TERMS     GDP-deflator adjustment. Never CPI — the standard is explicit
//                  about that, and deflating a food price by an index that
//                  contains food prices is circular.
//   KITCHEN UNITS  $/mt, $/cwt, $/kg -> $/lb, $/dozen, $/gallon. A kitchen does
//                  not buy tonnes. Conversions are exact, declared, and REFUSED
//                  where they would be a guess (see convertibleUnits).
//   SEASONALITY    Month-of-year distribution from monthly-or-finer data. This
//                  answers "when is a tomato cheap", and the data has been in
//                  the database the whole time — the old chart plotted a monthly
//                  series against a YEAR axis and threw the months away.
//
// Every function here is pure and total: unconvertible input returns the input
// unchanged plus an explicit reason, never a silently wrong number.
// =============================================================================

export interface Obs {
    /** ISO-ish date, 'YYYY-MM-DD' or 'YYYY-MM' or 'YYYY'. */
    date: string
    /** Calendar year, carried by the API alongside the date. */
    year: number
    price: number
}

// ---------------------------------------------------------------------------
// FREQUENCY
// ---------------------------------------------------------------------------

export type Frequency = 'daily' | 'weekly' | 'monthly' | 'annual'

export const FREQUENCIES: Frequency[] = ['daily', 'weekly', 'monthly', 'annual']

/** Default frequency filter. Annual is DEMOTED, not deleted: the user's brief is
 *  "annual is too infrequent for my chef friend to really dive in", so annual
 *  sources stay stored and reachable but are off by default (plan D9). */
export const DEFAULT_FREQUENCIES: Frequency[] = ['daily', 'weekly', 'monthly']

/** Normalize whatever a source catalog declares into one of four buckets.
 *  The coverage endpoint has historically emitted strings like 'annual+monthly'
 *  (NASS), which is not a frequency a filter can act on. */
export function normalizeFrequency(raw?: string | null): Frequency {
    const s = String(raw ?? '').toLowerCase()
    if (s.includes('dai')) return 'daily'
    if (s.includes('week')) return 'weekly'
    // 'annual+monthly' means an annual series that also has some monthly rows;
    // what the explorer can actually chart from it is the ANNUAL series, so it
    // is filtered as annual. Calling it monthly would smuggle it past a chef's
    // "no annual" filter.
    if (s.startsWith('annual') || s.includes('year')) return 'annual'
    if (s.includes('month')) return 'monthly'
    if (s.includes('annual')) return 'annual'
    return 'monthly'
}

export const FREQUENCY_LABEL: Record<Frequency, string> = {
    daily: 'Daily',
    weekly: 'Weekly',
    monthly: 'Monthly',
    annual: 'Annual',
}

/** Monthly-or-finer series carry a month-of-year signal worth showing. */
export function hasSeasonalSignal(f: Frequency): boolean {
    return f === 'daily' || f === 'weekly' || f === 'monthly'
}

// ---------------------------------------------------------------------------
// TRANSFORM CLUSTER — names + labels match ark-chart.js TRANSFORMS exactly
// ---------------------------------------------------------------------------

export type TransformKind = 'none' | 'reindex' | 'yoy' | 'rolling' | 'log'

export const TRANSFORMS: Array<{ key: TransformKind; label: string; hint: string }> = [
    { key: 'none', label: 'Level', hint: 'The price as published.' },
    { key: 'reindex', label: 'Reindex (=100)', hint: 'First plotted observation = 100.' },
    { key: 'yoy', label: 'YoY change %', hint: 'Percent change against the same period a year earlier.' },
    { key: 'rolling', label: 'Rolling avg', hint: 'Trailing average — smooths month-to-month noise.' },
    { key: 'log', label: 'Log scale', hint: 'Level on a log y-axis; equal vertical distance = equal percent change.' },
]

const finite = (v: unknown): number | null => {
    const n = typeof v === 'number' ? v : parseFloat(String(v))
    return Number.isFinite(n) ? n : null
}

function firstFinite(rows: Obs[]): number | null {
    for (const r of rows) {
        const n = finite(r.price)
        if (n !== null) return n
    }
    return null
}

/**
 * The observation one calendar year before `rows[i]`, matched BY DATE.
 *
 * This must not be a positional lag. Foodberg's BLS AP series carry real gaps —
 * `Tomatoes, field grown` has 552 observations across 47 years, so a naive
 * "twelve rows back" lands on 2025-05 when compared against 2026-06, and every
 * "vs a year ago" figure on the page would quietly be a 13-month change. The
 * lookup is exact on year-month for dated series, with a tolerance of one
 * period either side for weekly/daily data, and falls back to the previous
 * calendar year for annual series that carry only a year.
 */
function yearEarlier(rows: Obs[], i: number): Obs | null {
    const cur = rows[i]
    if (!cur) return null
    const s = String(cur.date)
    if (s.length >= 7 && s[4] === '-') {
        const targetY = cur.year - 1
        const targetM = s.slice(5, 7)
        // Search backwards: the match is always earlier in a sorted series.
        let best: Obs | null = null
        for (let j = i - 1; j >= 0; j--) {
            const r = rows[j]
            if (r.year < targetY) break
            const rs = String(r.date)
            if (r.year === targetY && rs.slice(5, 7) === targetM) {
                // For daily/weekly data several rows share a month; the closest
                // day-of-month wins, so a daily series compares like with like.
                if (!best) best = r
                else if (Math.abs(parseInt(rs.slice(8, 10) || '1', 10) - parseInt(s.slice(8, 10) || '1', 10))
                    < Math.abs(parseInt(String(best.date).slice(8, 10) || '1', 10) - parseInt(s.slice(8, 10) || '1', 10))) {
                    best = r
                }
            }
        }
        return best && Number.isFinite(best.price) ? best : null
    }
    // Year-only (annual) series.
    for (let j = i - 1; j >= 0; j--) {
        if (rows[j].year === cur.year - 1) return rows[j]
        if (rows[j].year < cur.year - 1) break
    }
    return null
}

/** Observations per year, inferred from the data itself rather than trusted from
 *  a label. Used for the rolling-average window and for frequency-shaped copy —
 *  NEVER for a year-over-year lag, which is date-matched (see yearEarlier). */
function periodsPerYear(rows: Obs[]): number {
    if (rows.length < 3) return 1
    const years = new Set(rows.map(r => r.year))
    const perYear = rows.length / Math.max(1, years.size)
    if (perYear >= 200) return 252   // daily
    if (perYear >= 40) return 52     // weekly
    if (perYear >= 6) return 12      // monthly
    if (perYear >= 3) return 4       // quarterly
    return 1                         // annual
}

/**
 * Apply one transform to a series. Returns a NEW array; the caller keeps the
 * original. Points that a transform cannot define (the first year of a YoY, a
 * non-positive value under log) are dropped rather than zero-filled.
 */
export function applyTransform(
    rows: Obs[],
    kind: TransformKind,
    opts: { rollingWindow?: number } = {},
): Obs[] {
    if (!rows.length || kind === 'none' || kind === 'log') return rows

    if (kind === 'reindex') {
        const base = firstFinite(rows)
        if (base === null || base === 0) return rows
        return rows.map(r => ({ ...r, price: (r.price / base) * 100 }))
    }

    if (kind === 'yoy') {
        const out: Obs[] = []
        for (let i = 0; i < rows.length; i++) {
            const prev = yearEarlier(rows, i)
            const cur = finite(rows[i]?.price)
            if (prev === null || prev.price === 0 || cur === null) continue
            out.push({ ...rows[i], price: (cur / prev.price - 1) * 100 })
        }
        return out
    }

    if (kind === 'rolling') {
        const win = opts.rollingWindow ?? Math.max(3, Math.round(periodsPerYear(rows) / 4))
        return rows.map((r, i) => {
            let sum = 0, n = 0
            for (let j = Math.max(0, i - win + 1); j <= i; j++) {
                const v = finite(rows[j].price)
                if (v !== null) { sum += v; n++ }
            }
            return { ...r, price: n ? sum / n : r.price }
        })
    }

    return rows
}

/** The y-axis unit after a transform. A transformed axis must NEVER keep the
 *  price unit — a YoY chart labelled "$ per lb" is a lie about what is plotted. */
export function transformedUnit(kind: TransformKind, unit: string): string {
    if (kind === 'reindex') return 'Index (first obs = 100)'
    if (kind === 'yoy') return '% change vs a year earlier'
    return unit
}

/** Log scale requires strictly positive values; report honestly rather than
 *  letting recharts silently drop them. */
export function logSafe(rows: Obs[]): { rows: Obs[]; dropped: number } {
    const kept = rows.filter(r => finite(r.price) !== null && r.price > 0)
    return { rows: kept, dropped: rows.length - kept.length }
}

// ---------------------------------------------------------------------------
// REAL TERMS — GDP deflator, never CPI
// ---------------------------------------------------------------------------

export interface DeflatorPoint { date: string; value: number }

export interface Deflator {
    series_id: string
    name: string
    publisher: string
    frequency: string
    base_period?: string
    coverage?: { start: string; end: string }
    latest?: { date: string; value: number }
    data: DeflatorPoint[]
    note?: string
}

const ymKey = (d: string): string => String(d).slice(0, 7)

/**
 * Build a month -> deflator-level lookup from a quarterly deflator by holding
 * each quarter's level across its three months. Holding (rather than
 * interpolating) is the conservative choice: it never invents a level the BEA
 * did not publish, and the error it can introduce is bounded by one quarter of
 * inflation.
 */
function monthlyDeflatorIndex(def: Deflator): Map<string, number> {
    const idx = new Map<string, number>()
    for (const p of def.data) {
        const v = finite(p.value)
        if (v === null) continue
        const y = parseInt(String(p.date).slice(0, 4), 10)
        const m = parseInt(String(p.date).slice(5, 7), 10) || 1
        if (!Number.isFinite(y)) continue
        const span = /quarter/i.test(def.frequency) ? 3 : 1
        for (let k = 0; k < span; k++) {
            const mm = m + k
            const yy = y + Math.floor((mm - 1) / 12)
            const m2 = ((mm - 1) % 12) + 1
            idx.set(`${yy}-${String(m2).padStart(2, '0')}`, v)
        }
    }
    return idx
}

export interface RealResult {
    rows: Obs[]
    /** Observations dropped because they PRE-DATE the deflator (GDPDEF starts
     *  1947; Foodberg's NASS farm-gate series reach back to 1908). */
    dropped: number
    /** Observations NEWER than the last published deflator quarter, carried at
     *  that quarter's level. Disclosed separately because it is an
     *  approximation, not a drop. */
    carried: number
    /** The last deflator period actually published, e.g. "2026-01". */
    deflatorEnd: string | null
    /** The dollar-period the series is expressed in, e.g. "2026-01". */
    baseLabel: string | null
    /** Present when real terms could not be produced at all. */
    unavailable?: string
}

/** How far past the last published deflator quarter a price may still be
 *  expressed in constant dollars by holding that quarter's level. Two quarters
 *  is the realistic BEA publication lag; beyond that the approximation stops
 *  being one and the observation is dropped instead. */
const MAX_CARRY_MONTHS = 6

/** Whole months from `a` to `b`, both 'YYYY-MM'. */
function monthsBetween(a: string, b: string): number {
    const [ay, am] = [parseInt(a.slice(0, 4), 10), parseInt(a.slice(5, 7), 10)]
    const [by, bm] = [parseInt(b.slice(0, 4), 10), parseInt(b.slice(5, 7), 10)]
    return (by - ay) * 12 + (bm - am)
}

/**
 * Convert a nominal series to constant dollars of the deflator's latest period.
 *
 * The deflator does not cover the series at either end, and the two ends need
 * opposite treatment:
 *
 *   BEFORE the deflator starts — GDPDEF begins 1947-Q1 and Foodberg's NASS
 *     farm-gate series reach back to 1908. Those observations are DROPPED and
 *     counted. Deflating a 1908 price with a 1947 level, or quietly reverting
 *     to nominal for the early years of the same line, would both be worse than
 *     a shorter honest series.
 *
 *   AFTER the deflator ends — BEA publishes GDPDEF quarterly and with a lag, so
 *     the most recent monthly food prices are always newer than the newest
 *     deflator quarter. Dropping them would delete the LATEST price from the
 *     real view, which is the one number a chef came for. Those observations
 *     are carried at the last published level (the same holding operation
 *     already applied within a quarter), counted separately, and disclosed —
 *     for up to MAX_CARRY_MONTHS, beyond which they are dropped too.
 *
 * The caller is expected to say both numbers out loud on the page.
 */
export function toRealTerms(rows: Obs[], def: Deflator | null): RealResult {
    const none = { dropped: 0, carried: 0, deflatorEnd: null, baseLabel: null }
    if (!def || !def.data?.length) {
        return { rows, ...none, unavailable: 'The GDP deflator is not available, so real-terms adjustment is off.' }
    }
    const idx = monthlyDeflatorIndex(def)
    // Base = the most recent published deflator level, so the chart reads in
    // today's money rather than in some arbitrary historical base year.
    const baseDate = def.latest?.date ?? def.data[def.data.length - 1]?.date
    const baseLevel = finite(def.latest?.value ?? def.data[def.data.length - 1]?.value)
    if (!baseDate || baseLevel === null || baseLevel === 0) {
        return { rows, ...none, unavailable: 'The GDP deflator has no usable base period.' }
    }
    // Last month the published deflator actually reaches (a quarter spans three).
    const lastCovered = [...idx.keys()].sort().pop() ?? ymKey(baseDate)

    const out: Obs[] = []
    let dropped = 0
    let carried = 0
    for (const r of rows) {
        // An annual observation is deflated at mid-year, the standard
        // convention for an annual average.
        const key = String(r.date).length >= 7 ? ymKey(r.date) : `${r.year}-06`
        let level = idx.get(key) ?? idx.get(`${r.year}-06`)
        if (level === undefined) {
            const past = monthsBetween(lastCovered, key)
            if (past > 0 && past <= MAX_CARRY_MONTHS) {
                level = idx.get(lastCovered)
                carried++
            }
        }
        if (level === undefined || level === 0) { dropped++; continue }
        out.push({ ...r, price: (r.price * baseLevel) / level })
    }
    return {
        rows: out, dropped, carried,
        deflatorEnd: lastCovered,
        baseLabel: ymKey(baseDate),
    }
}

// ---------------------------------------------------------------------------
// KITCHEN UNITS
// ---------------------------------------------------------------------------

export interface UnitOption {
    /** What the axis and tooltips say. */
    label: string
    /** Multiply the native price by this to get the target unit. 1 = native. */
    factor: number
    /** True for the publisher's own unit — always offered, always labelled. */
    native?: boolean
}

const LB_PER_KG = 2.2046226218
const LB_PER_MT = 2204.6226218
const LB_PER_TONNE = LB_PER_MT   // FAOSTAT's "tonne" is a metric tonne

/** Bushel weights are commodity-specific and legally defined; there is no
 *  generic $/bu -> $/lb factor. Anything not in this table gets NO bushel
 *  conversion offered, which is the honest outcome. */
const BUSHEL_LB: Record<string, number> = {
    wheat: 60, soybeans: 60, 'soybean': 60, rye: 56, corn: 56, maize: 56,
    sorghum: 56, barley: 48, oats: 32,
}

const normUnit = (u?: string | null): string =>
    String(u ?? '').toLowerCase().replace(/[()\s]/g, '')

/**
 * Which units this series can honestly be shown in.
 *
 * The first entry is what the explorer selects by default: a kitchen unit where
 * one exists, the native unit otherwise. An index, a percentage, or an unknown
 * unit gets exactly one option — its own — because converting it would be
 * fabrication. The publisher's native unit is ALWAYS in the list, so the reader
 * can always get back to the number the publisher actually published.
 */
export function convertibleUnits(nativeUnit: string | null | undefined, slug?: string): UnitOption[] {
    const native: UnitOption = { label: nativeUnit?.trim() || 'Unknown unit', factor: 1, native: true }
    const u = normUnit(nativeUnit)
    if (!u) return [native]

    // Already a kitchen unit — nothing to do, but offer the metric sibling.
    if (u === '$perlb' || u === '$/lb') {
        return [native, { label: '$ per kg', factor: LB_PER_KG }]
    }
    if (u === '$per16oz') {
        // 16 oz IS a pound; relabel rather than pretend it is a different unit.
        return [{ label: '$ per lb', factor: 1 }, native, { label: '$ per kg', factor: LB_PER_KG }]
    }
    if (u === '$per8oz') {
        return [{ label: '$ per lb', factor: 2 }, native, { label: '$ per kg', factor: 2 * LB_PER_KG }]
    }
    if (u === '$perdozen') return [native, { label: '$ per egg', factor: 1 / 12 }]
    if (u === '$pergallon') return [native, { label: '$ per quart', factor: 1 / 4 }, { label: '$ per litre', factor: 1 / 3.785411784 }]
    if (u === '$per1/2gallon') {
        return [{ label: '$ per gallon', factor: 2 }, native, { label: '$ per litre', factor: 2 / 3.785411784 }]
    }

    // Bulk / global units -> the kitchen.
    if (u === '$/mt' || u === 'usd/mt' || u === '$permetricton') {
        return [{ label: '$ per lb', factor: 1 / LB_PER_MT }, native, { label: '$ per kg', factor: 1 / 1000 }]
    }
    if (u === 'usd/tonne' || u === '$/tonne' || u === '$/t') {
        return [{ label: '$ per lb', factor: 1 / LB_PER_TONNE }, native, { label: '$ per kg', factor: 1 / 1000 }]
    }
    if (u === '$/kg' || u === 'usd/kg') {
        return [{ label: '$ per lb', factor: 1 / LB_PER_KG }, native]
    }
    if (u.includes('cwt')) {
        // hundredweight = 100 lb
        return [{ label: '$ per lb', factor: 1 / 100 }, native]
    }
    if (u.includes('bu') && slug) {
        const lb = BUSHEL_LB[slug.toLowerCase()]
        if (lb) return [{ label: '$ per lb', factor: 1 / lb }, native]
        // Unknown bushel weight -> refuse. A generic factor would be a guess.
        return [native]
    }
    if (u.includes('ton') && !u.includes('tonne')) {
        // US short ton = 2000 lb. Only when the string is unambiguous.
        if (u.includes('shortton') || u === '$/ton') {
            return [{ label: '$ per lb', factor: 1 / 2000 }, native]
        }
    }

    // Indices, percentages, 'USD per unit', 'various', anything unrecognised:
    // exactly one option, the publisher's own.
    return [native]
}

export function convert(rows: Obs[], factor: number): Obs[] {
    if (factor === 1) return rows
    return rows.map(r => ({ ...r, price: r.price * factor }))
}

// ---------------------------------------------------------------------------
// SEASONALITY — "when is a tomato cheap"
// ---------------------------------------------------------------------------

export const MONTH_NAMES = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

export interface SeasonalMonth {
    month: number          // 1-12
    name: string
    n: number              // how many years contributed
    median: number
    p25: number
    p75: number
    min: number
    max: number
    /** Median as a percent of the all-month median — >100 = dearer than typical. */
    indexed: number
    /** The most recent year's value for this month, where the series has one. */
    latestYear?: number
}

export interface Seasonality {
    months: SeasonalMonth[]
    /** Years actually used (the trailing window), for honest labelling. */
    yearsUsed: number
    yearFrom: number
    yearTo: number
    cheapest: SeasonalMonth | null
    dearest: SeasonalMonth | null
    /** Spread between the dearest and cheapest median, as a percent of cheapest. */
    swingPct: number | null
    /** Where the latest observation sits in its own month's historical range. */
    currentPercentile: number | null
    currentMonth: SeasonalMonth | null
}

function quantile(sorted: number[], q: number): number {
    if (!sorted.length) return NaN
    const pos = (sorted.length - 1) * q
    const lo = Math.floor(pos), hi = Math.ceil(pos)
    if (lo === hi) return sorted[lo]
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo)
}

/**
 * Month-of-year distribution over a trailing window of complete-enough years.
 *
 * `windowYears` defaults to 20: long enough to be a distribution, short enough
 * that a 1980s price level does not dominate a 2026 seasonal shape. A month is
 * only reported when at least 3 years contributed to it, so a thin series
 * produces a short, honest seasonal profile rather than a confident-looking
 * one drawn from two observations.
 */
export function seasonality(rows: Obs[], windowYears = 20): Seasonality | null {
    const dated = rows.filter(r => String(r.date).length >= 7)
    if (dated.length < 24) return null

    const maxYear = Math.max(...dated.map(r => r.year))
    const minYear = Math.max(Math.min(...dated.map(r => r.year)), maxYear - windowYears + 1)
    const win = dated.filter(r => r.year >= minYear)

    const byMonth = new Map<number, Obs[]>()
    for (const r of win) {
        const m = parseInt(String(r.date).slice(5, 7), 10)
        if (!m || m < 1 || m > 12) continue
        const list = byMonth.get(m) ?? []
        list.push(r)
        byMonth.set(m, list)
    }

    const months: SeasonalMonth[] = []
    for (let m = 1; m <= 12; m++) {
        const obs = byMonth.get(m) ?? []
        // Daily/weekly data gives many observations per month-year; count YEARS.
        const nYears = new Set(obs.map(o => o.year)).size
        if (nYears < 3) continue
        const vals = obs.map(o => o.price).filter(v => Number.isFinite(v)).sort((a, b) => a - b)
        if (!vals.length) continue
        const latestYearObs = obs.filter(o => o.year === maxYear)
        months.push({
            month: m,
            name: MONTH_NAMES[m - 1],
            n: nYears,
            median: quantile(vals, 0.5),
            p25: quantile(vals, 0.25),
            p75: quantile(vals, 0.75),
            min: vals[0],
            max: vals[vals.length - 1],
            indexed: 0, // filled below
            latestYear: latestYearObs.length
                ? latestYearObs.reduce((s, o) => s + o.price, 0) / latestYearObs.length
                : undefined,
        })
    }
    if (months.length < 6) return null   // not a seasonal profile, just a few months

    const allMedians = months.map(m => m.median).sort((a, b) => a - b)
    const grand = quantile(allMedians, 0.5)
    for (const m of months) m.indexed = grand ? (m.median / grand) * 100 : 100

    const cheapest = months.reduce((a, b) => (b.median < a.median ? b : a), months[0])
    const dearest = months.reduce((a, b) => (b.median > a.median ? b : a), months[0])
    const swingPct = cheapest.median > 0
        ? ((dearest.median - cheapest.median) / cheapest.median) * 100
        : null

    // Where does the latest observation sit within its own month's history?
    const latest = dated[dated.length - 1]
    const latestMonthNo = parseInt(String(latest.date).slice(5, 7), 10)
    const currentMonth = months.find(m => m.month === latestMonthNo) ?? null
    let currentPercentile: number | null = null
    if (currentMonth) {
        const obs = (byMonth.get(latestMonthNo) ?? []).map(o => o.price).sort((a, b) => a - b)
        if (obs.length >= 3) {
            const below = obs.filter(v => v < latest.price).length
            currentPercentile = (below / obs.length) * 100
        }
    }

    return {
        months,
        yearsUsed: maxYear - minYear + 1,
        yearFrom: minYear,
        yearTo: maxYear,
        cheapest,
        dearest,
        swingPct,
        currentPercentile,
        currentMonth,
    }
}

// ---------------------------------------------------------------------------
// HEADLINE DELTAS — now / vs last month / vs last year / vs 5-yr average
// ---------------------------------------------------------------------------

export interface Deltas {
    latest: Obs | null
    vsPrevious: { pct: number; from: Obs; label: string } | null
    vsYearAgo: { pct: number; from: Obs; label: string } | null
    vsFiveYearAvg: { pct: number; avg: number; years: number } | null
    allTimeLow: Obs | null
    allTimeHigh: Obs | null
}

export function deltas(rows: Obs[], freq: Frequency): Deltas {
    const empty: Deltas = {
        latest: null, vsPrevious: null, vsYearAgo: null,
        vsFiveYearAvg: null, allTimeLow: null, allTimeHigh: null,
    }
    if (!rows.length) return empty
    const latest = rows[rows.length - 1]

    const prev = rows.length >= 2 ? rows[rows.length - 2] : null
    // Date-matched, never positional — see yearEarlier(). A positional lag on a
    // gapped BLS series reports a 13-month change as "vs a year ago".
    const yearAgo = yearEarlier(rows, rows.length - 1)

    const prevLabel = freq === 'annual' ? 'vs last year'
        : freq === 'monthly' ? 'vs last month'
            : freq === 'weekly' ? 'vs last week' : 'vs previous day'

    // Five-year average over the trailing 5 calendar years, excluding the
    // current (incomplete) year so a part-year does not distort the baseline.
    const curYear = latest.year
    const window = rows.filter(r => r.year >= curYear - 5 && r.year < curYear)
    const yearsIn = new Set(window.map(r => r.year)).size
    const avg = window.length ? window.reduce((s, r) => s + r.price, 0) / window.length : null

    const low = rows.reduce((a, b) => (b.price < a.price ? b : a), rows[0])
    const high = rows.reduce((a, b) => (b.price > a.price ? b : a), rows[0])

    return {
        latest,
        vsPrevious: prev && prev.price !== 0
            ? { pct: (latest.price / prev.price - 1) * 100, from: prev, label: prevLabel }
            : null,
        vsYearAgo: yearAgo && yearAgo.price !== 0 && yearAgo !== latest
            ? { pct: (latest.price / yearAgo.price - 1) * 100, from: yearAgo, label: 'vs a year ago' }
            : null,
        vsFiveYearAvg: avg && avg !== 0 && yearsIn >= 2
            ? { pct: (latest.price / avg - 1) * 100, avg, years: yearsIn }
            : null,
        allTimeLow: low,
        allTimeHigh: high,
    }
}

// ---------------------------------------------------------------------------
// RANGE
// ---------------------------------------------------------------------------

export type RangeKey = '1y' | '5y' | '10y' | '25y' | 'max'

export const RANGES: Array<{ key: RangeKey; label: string; years: number | null }> = [
    { key: '1y', label: '1Y', years: 1 },
    { key: '5y', label: '5Y', years: 5 },
    { key: '10y', label: '10Y', years: 10 },
    { key: '25y', label: '25Y', years: 25 },
    { key: 'max', label: 'Max', years: null },
]

export function clipToRange(rows: Obs[], key: RangeKey): Obs[] {
    const spec = RANGES.find(r => r.key === key)
    if (!spec?.years || !rows.length) return rows
    const maxYear = rows[rows.length - 1].year
    return rows.filter(r => r.year > maxYear - spec.years!)
}

// ---------------------------------------------------------------------------
// FORMATTING
// ---------------------------------------------------------------------------

export function fmtPrice(v: number | null | undefined, unit?: string): string {
    if (v == null || !Number.isFinite(v)) return '—'
    const digits = Math.abs(v) >= 100 ? 0 : Math.abs(v) >= 1 ? 2 : 3
    const n = v.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })
    if (!unit) return n
    // '$ per lb' -> '$2.15 / lb'
    const m = /^\$\s*per\s+(.*)$/i.exec(unit.trim())
    if (m) return `$${n} / ${m[1]}`
    return `${n} ${unit}`
}

export function fmtPct(v: number | null | undefined): string {
    if (v == null || !Number.isFinite(v)) return '—'
    const sign = v > 0 ? '+' : ''
    return `${sign}${v.toLocaleString(undefined, { maximumFractionDigits: 1 })}%`
}

/** A month label for a chart axis: '2026-06' -> "Jun 2026". */
export function fmtMonth(date: string): string {
    const s = String(date)
    const y = s.slice(0, 4)
    const m = parseInt(s.slice(5, 7), 10)
    if (!m || s.length < 7) return y
    return `${MONTH_NAMES[m - 1]} ${y}`
}
