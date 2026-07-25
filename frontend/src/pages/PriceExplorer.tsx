import { BarChart3, Pin, Search, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
    Area,
    CartesianGrid,
    ComposedChart,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis,
} from 'recharts'
import { api } from '../services/api'
import { useArkTheme } from '../arcanum/arkChartTheme'
import ArkDownloads from '../arcanum/ArkDownloads'
import { ChartMetaStrip, ScrollableDataTable } from '../components/ChartDetails'
import {
    DEFAULT_FREQUENCIES, FREQUENCIES, FREQUENCY_LABEL, RANGES, TRANSFORMS,
    applyTransform, clipToRange, convert, convertibleUnits, deltas, fmtMonth, fmtPct, fmtPrice,
    hasSeasonalSignal, logSafe, normalizeFrequency, seasonality, toRealTerms, transformedUnit,
    type Deflator, type Frequency, type Obs, type RangeKey, type RealResult, type TransformKind,
    type UnitOption,
} from '../arcanum/arkTransforms'

// ---------------------------------------------------------------------------
// THE PRICE EXPLORER — Foodberg's home page.
//
// This page IS `/`. It is not a landing page that links to a tool; it is the
// tool, and it renders a real price on load. Before the 2026-07-25 chef-first
// flip, `/` was a hero + two download buttons + a feature grid, and the first
// nav item was a composite INDEX — a chef's first click landed on a number that
// is not a price, in units nobody buys, against a base period from 1982.
//
// The brief for this page was explicit: "maximum detail and maximum options,
// well organized and thoughtfully arranged, front and center." So every control
// is visible at once. Nothing is hidden behind an "advanced" disclosure —
// maximum options only means anything if the options are discoverable. The
// design problem here is ORGANIZATION, not reduction.
//
// Three zones, all reachable without scrolling on a desktop viewport:
//   FIND   search + kitchen categories + frequency filter + the commodity list
//   CHART  the hero series, with the whole control cluster above it
//   RAIL   deltas, seasonality, every source, regions, the wholesale wedge,
//          provenance
// On mobile the find column becomes a collapsible sheet and the rail becomes
// accordions: density degrades, it does not disappear.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// KITCHEN TAXONOMY
//
// Replaces the USDA commodity taxonomy this page shipped with, which was built
// for an agricultural-statistics audience and not a kitchen: "Fiber" was cotton,
// "Other" held hay and tobacco, and there was NO produce category at all — the
// only vegetable in the whole taxonomy was potatoes, filed under "Other".
//
// Every slug the coverage endpoint can return is classified. Explicit overrides
// come first; anything unmatched falls through to keyword rules and finally to
// "Specialty & Non-Food", so a newly-ingested item is never silently dropped
// from the category filter.
// ---------------------------------------------------------------------------

export const KITCHEN_CATEGORIES = [
    'Produce',
    'Protein',
    'Dairy & Eggs',
    'Dry Goods',
    'Oils & Fats',
    'Sweeteners',
    'Beverages',
    'Specialty & Non-Food',
] as const

export type KitchenCategory = typeof KITCHEN_CATEGORIES[number]

// Exact slug -> category. Only for items whose keywords are ambiguous or absent.
const CATEGORY_OVERRIDES: Record<string, KitchenCategory> = {
    // Produce
    apples: 'Produce', avocados: 'Produce', bananas: 'Produce', cabbage: 'Produce',
    celery: 'Produce', cranberries: 'Produce', grapefruit: 'Produce', grapes: 'Produce',
    lemons: 'Produce', mushrooms: 'Produce', oranges: 'Produce', peaches: 'Produce',
    potatoes: 'Produce', strawberries: 'Produce', 'sweet potatoes': 'Produce',
    // Protein
    cattle: 'Protein', chickens: 'Protein', hogs: 'Protein', sheep: 'Protein',
    turkeys: 'Protein',
    // Dairy & eggs
    eggs: 'Dairy & Eggs', milk: 'Dairy & Eggs',
    // Dry goods (grains, pulses, nuts, flours, bakery, pasta)
    almonds: 'Dry Goods', barley: 'Dry Goods', corn: 'Dry Goods', lentils: 'Dry Goods',
    maize: 'Dry Goods', millet: 'Dry Goods', oats: 'Dry Goods', peanuts: 'Dry Goods',
    peas: 'Dry Goods', rice: 'Dry Goods', rye: 'Dry Goods', sorghum: 'Dry Goods',
    soybeans: 'Dry Goods', walnuts: 'Dry Goods', wheat: 'Dry Goods',
    // Oils & fats (oilseeds crushed for oil)
    canola: 'Oils & Fats', flaxseed: 'Oils & Fats', rapeseed: 'Oils & Fats',
    safflower: 'Oils & Fats', sunflower: 'Oils & Fats',
    // Sweeteners
    honey: 'Sweeteners', sugar: 'Sweeteners', sugarcane: 'Sweeteners',
    // Beverages
    coffee: 'Beverages',
    // Non-food agricultural output — real data, but not a kitchen input.
    cotton: 'Specialty & Non-Food', hay: 'Specialty & Non-Food',
    mohair: 'Specialty & Non-Food', tobacco: 'Specialty & Non-Food',
    wool: 'Specialty & Non-Food',
}

// Ordered keyword rules, applied to `<slug> <publisher item name>` lowercased.
// First match wins, so more specific terms are listed before broader ones.
const CATEGORY_RULES: Array<[KitchenCategory, string[]]> = [
    ['Beverages', ['coffee', 'juice', 'tea', 'cocoa', 'soda']],
    ['Sweeteners', ['sugar', 'honey', 'syrup', 'molasses']],
    ['Dairy & Eggs', ['cheese', 'milk', 'butter', 'yogurt', 'ice cream', 'cream', 'egg']],
    ['Protein', [
        'beef', 'steak', 'roast', 'bacon', 'ham', 'pork', 'chicken', 'turkey',
        'sausage', 'tuna', 'fish', 'shrimp', 'lamb', 'veal', 'frankfurter',
    ]],
    ['Produce', [
        'tomato', 'lettuce', 'onion', 'pepper', 'carrot', 'cabbage', 'celery',
        'potato', 'banana', 'orange', 'lemon', 'grapefruit', 'apple', 'peach',
        'grape', 'berr', 'melon', 'broccoli', 'cucumber', 'mushroom', 'squash',
        'bean', 'greens', 'herb', 'avocado', 'lime',
    ]],
    ['Oils & Fats', ['oil', 'shortening', 'margarine', 'lard', 'canola', 'sunflower']],
    ['Dry Goods', [
        'bread', 'flour', 'rice', 'wheat', 'corn', 'oat', 'barley', 'pasta',
        'spaghetti', 'macaroni', 'cereal', 'cookie', 'cupcake', 'cracker',
        'chips', 'peanut butter', 'lentil', 'nut', 'grain', 'sorghum', 'rye',
    ]],
]

export function classifyCommodity(slug: string, label?: string): KitchenCategory {
    const override = CATEGORY_OVERRIDES[slug]
    if (override) return override
    const hay = `${slug.replace(/-/g, ' ')} ${label ?? ''}`.toLowerCase()
    for (const [category, keywords] of CATEGORY_RULES) {
        if (keywords.some(k => hay.includes(k))) return category
    }
    return 'Specialty & Non-Food'
}

// One browsable row in the commodity list. Derived from /api/prices/coverage,
// which is the authoritative multi-source map — NOT from the WASDE commodity
// list, which is the USDA universe and contains no tomatoes.
interface ExplorerItem {
    slug: string
    label: string
    category: KitchenCategory
    /** The finest frequency any of this item's sources offers. */
    bestFreq: Frequency
}

// A distinct item name returned by the real /api/prices/search endpoint,
// reduced from raw observation rows.
interface SearchHit {
    name: string
    source: string
    observations: number
    latest?: string
    slug?: string
}

// Liveness is computed by the backend (worldbank_client._liveness) from the
// series' LAST REAL OBSERVATION measured against the newest observation in its
// own source catalog — never from a declared end_year or from membership in a
// publisher's item list. Surfacing all 47 BLS AP items means surfacing the ~15
// that BLS quietly stopped publishing between 2017 and 2024, so the badge is
// not optional decoration: without it the page would present a 1997 carrot
// price as a current one.
interface Liveness {
    status: 'live' | 'stale' | 'discontinued' | 'unknown'
    months_behind: number | null
    last_real_observation: string | null
}

interface SourceCov {
    points: number
    frequency: string
    /** Normalized daily|weekly|monthly|annual, added by the backend. Older
     *  builds only had `frequency`, so this is derived defensively below. */
    freq?: string
    start: string
    end: string
    label?: string
    n_years?: number
    unit?: string
    liveness?: Liveness
}

// Light- and dark-mode pairs: a staleness badge that is invisible in one theme
// is worse than no badge, because the page then silently presents a 2017 price
// as current.
const LIVENESS_STYLE: Record<string, string> = {
    stale: 'text-amber-800 bg-amber-100 dark:text-amber-700 dark:text-amber-300 dark:bg-amber-900/40',
    discontinued: 'text-rose-800 bg-rose-100 dark:text-rose-700 dark:text-rose-300 dark:bg-rose-900/40',
    unknown: 'text-ark-fg-dim bg-ark-tag',
}

function livenessNote(l?: Liveness): string | null {
    if (!l || l.status === 'live') return null
    const behind = l.months_behind != null ? `${l.months_behind} months behind` : 'age unknown'
    const last = l.last_real_observation ? l.last_real_observation.slice(0, 7) : 'unknown'
    if (l.status === 'discontinued') return `Discontinued — last real value ${last} (${behind})`
    if (l.status === 'stale') return `Stale — last real value ${last} (${behind})`
    return `Liveness unknown — last value ${last}`
}

type SourceKey = 'av' | 'nass' | 'pinksheet' | 'retail'
type Coverage = Partial<Record<SourceKey, SourceCov>>

interface SourcePayload {
    commodity: string
    source: string
    has_history: boolean
    label?: string
    unit?: string | null
    data_points: number
    date_range?: { start: string; end: string }
    data: Obs[]
    note?: string
}

const SOURCE_LABELS: Record<string, string> = {
    nass: 'US farm gate (USDA)',
    av: 'Global spot (monthly)',
    pinksheet: 'Global spot (Pink Sheet)',
    retail: 'US retail (BLS)',
}

// Preferred display order for source tabs. Retail first: it is the only source
// quoted in units a kitchen actually buys in, and it is the one a chef wants.
const SOURCE_ORDER: SourceKey[] = ['retail', 'pinksheet', 'av', 'nass']

// Commodities with a genuine multi-year Alpha-Vantage spot-price series
// (1992→present monthly), per the backend /api/prices/history contract.
const AV_HISTORY_COMMODITIES = new Set(['wheat', 'corn', 'coffee', 'sugar', 'cotton'])

// The item that renders on load. "A real price renders on load. No empty state,
// no 'select a commodity to begin.'" Tomatoes are the canonical case: 552
// monthly BLS observations, 1980-01 → 2026-06, in $ per lb — and the item that
// used to return "Commodities (0)" while sitting in the database the whole time.
const DEFAULT_ITEM = 'tomatoes-field-grown'
const DEFAULT_SOURCE: SourceKey = 'retail'

// --- detail-rail payload (/api/prices/detail/{slug}) ------------------------
// Served by the backend so the rail can show sources, regional variants and the
// farm -> wholesale -> retail wedge without the client issuing six requests.
// Every field is optional: the page must render correctly against a backend
// that predates this endpoint, and it does (the rail simply shows less).
interface DetailSource {
    key: string; label: string; frequency: string; unit?: string | null
    points: number; start?: string; end?: string; liveness?: Liveness
}
interface DetailRegional {
    slug: string; label: string; region?: string; unit?: string | null
    latest?: { date: string; price: number }; points?: number
}
interface PriceDetail {
    slug: string; label?: string; unit?: string | null
    sources?: DetailSource[]
    regional?: DetailRegional[]
    wedge?: {
        retail?: { label?: string; series?: string; unit?: string; latest?: { date: string; price: number } } | null
        ppi?: { series_id?: string; label?: string; unit?: string; latest?: { date: string; value: number } } | null
        wholesale?: {
            commodity?: string; cities?: number; rows?: number; latest_date?: string
            low?: number; high?: number; unit?: string; varieties?: number
        } | null
    }
    provenance?: {
        publisher?: string; series_id_or_item?: string; retrieval_url?: string
        geography?: string; unit?: string
    }
    note?: string
}

/** A labelled block in the detail rail. Collapsible on mobile (<details>),
 *  always open on desktop — the rail is the "maximum options" surface and must
 *  not hide itself from the audience it exists for. */
function RailBlock({ title, children, badge }: {
    title: string; children: React.ReactNode; badge?: React.ReactNode
}) {
    return (
        <details open className="ark-rail-block border border-ark-line rounded-lg bg-ark-bg-soft">
            <summary className="cursor-pointer list-none px-3 py-2 flex items-center justify-between gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-ark-fg-dim">{title}</span>
                {badge}
            </summary>
            <div className="px-3 pb-3 pt-1">{children}</div>
        </details>
    )
}

// The kit ships a light AND a dark theme, and a badge must be legible in both.
// A dark-only palette (light text on a 30%-alpha dark fill) renders as pale-on-
// pale over the light theme's white page — legible in review, invisible to half
// the audience. Every tone therefore carries an explicit light-mode pair.
function FreqBadge({ freq }: { freq: Frequency }) {
    const tone = freq === 'daily'
        ? 'text-emerald-800 bg-emerald-100 dark:text-emerald-700 dark:text-emerald-300 dark:bg-emerald-900/40'
        : freq === 'weekly'
            ? 'text-teal-800 bg-teal-100 dark:text-teal-300 dark:bg-teal-900/40'
            : freq === 'monthly'
                ? 'text-sky-800 bg-sky-100 dark:text-sky-300 dark:bg-sky-900/40'
                : 'text-ark-fg-dim bg-ark-tag'
    return (
        <span className={`shrink-0 text-[10px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded ${tone}`}>
            {FREQUENCY_LABEL[freq]}
        </span>
    )
}

export default function PriceExplorer() {
    const [coverage, setCoverage] = useState<Record<string, Coverage>>({})
    const [displayNames, setDisplayNames] = useState<Record<string, string>>({})
    const [loading, setLoading] = useState(true)
    const [series, setSeries] = useState<SourcePayload | null>(null)
    const [detail, setDetail] = useState<PriceDetail | null>(null)
    const [deflator, setDeflator] = useState<Deflator | null>(null)
    const [selectedCommodity, setSelectedCommodity] = useState<string | null>(null)
    const [selectedSource, setSelectedSource] = useState<string>(DEFAULT_SOURCE)
    const [fallbackValue, setFallbackValue] = useState<{ price: number; year: number; unit: string } | null>(null)
    const [searchHits, setSearchHits] = useState<SearchHit[] | null>(null)
    const [searching, setSearching] = useState(false)
    const [findOpen, setFindOpen] = useState(false)   // mobile bottom-sheet state
    const [searchParams, setSearchParams] = useSearchParams()
    const t = useArkTheme()

    // ---- URL is the single source of truth for every view control -----------
    // "Every state (item, unit, transform, range, comparison set) round-trips
    // through the URL." Reading from searchParams rather than mirroring it into
    // local state is what makes a pasted link reproduce the exact view.
    const qp = (k: string, fallback: string) => searchParams.get(k) ?? fallback
    const searchTerm = qp('q', '')
    const selectedCategory = qp('cat', 'all')
    const transform = qp('t', 'none') as TransformKind
    const range = qp('r', 'max') as RangeKey
    const real = qp('real', '0') === '1'
    const unitIdx = parseInt(qp('u', '0'), 10) || 0
    const freqFilter = useMemo<Set<Frequency>>(() => {
        const raw = searchParams.get('freq')
        if (raw === 'all') return new Set(FREQUENCIES)
        if (!raw) return new Set(DEFAULT_FREQUENCIES)
        const picked = raw.split(',').filter(f => (FREQUENCIES as string[]).includes(f)) as Frequency[]
        return new Set(picked.length ? picked : DEFAULT_FREQUENCIES)
    }, [searchParams])
    const pinned = useMemo<string[]>(
        () => (searchParams.get('pin') || '').split(',').filter(Boolean), [searchParams])

    const setParam = useCallback((patch: Record<string, string | null>) => {
        setSearchParams(prev => {
            const next = new URLSearchParams(prev)
            for (const [k, v] of Object.entries(patch)) {
                if (v === null || v === '') next.delete(k)
                else next.set(k, v)
            }
            return next
        }, { replace: true })
    }, [setSearchParams])

    // ---- data load ----------------------------------------------------------
    useEffect(() => {
        api.getPriceCoverage()
            .then((covRes) => {
                setCoverage(covRes.data.commodities || {})
                setDisplayNames(covRes.data.display_names || {})
            })
            .catch((error) => console.error('Failed to load commodities:', error))
            .finally(() => setLoading(false))
        // The deflator powers the nominal/real toggle. Its absence is not an
        // error — the toggle simply reports that real terms are unavailable.
        api.getDeflator()
            .then(res => {
                const d = res.data
                if (d && Array.isArray(d.data) && d.data.length) setDeflator(d as Deflator)
            })
            .catch(() => setDeflator(null))
    }, [])

    const covFor = useCallback(
        (name: string): Coverage => coverage[name.toLowerCase()] ?? {}, [coverage])

    // A source is plottable only if it spans ≥2 distinct years (a real time
    // series). Prefer the explicit n_years count; fall back to points > 1 when
    // n_years isn't reported. This excludes WASDE-2025-only single-year series.
    const isMultiYear = (c?: SourceCov): boolean =>
        !!c && (c.n_years !== undefined ? c.n_years >= 2 : c.points > 1)

    const sourcesFor = useCallback(
        (name: string) => SOURCE_ORDER.filter((s) => isMultiYear(covFor(name)[s])), [covFor])

    /** Normalized frequency of one source, tolerant of a backend that has not
     *  yet shipped the `freq` field. */
    const freqOf = useCallback((slug: string, key: SourceKey): Frequency => {
        const c = covFor(slug)[key]
        return normalizeFrequency(c?.freq ?? c?.frequency)
    }, [covFor])

    /** Finest frequency across an item's plottable sources. */
    const bestFreqFor = useCallback((slug: string): Frequency => {
        const order: Frequency[] = ['daily', 'weekly', 'monthly', 'annual']
        const found = sourcesFor(slug).map(s => freqOf(slug, s))
        for (const f of order) if (found.includes(f)) return f
        return 'annual'
    }, [sourcesFor, freqOf])

    const loadSeries = useCallback(async (commodity: string, source: string) => {
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
    }, [])

    const selectCommodity = useCallback((commodity: string, source?: string) => {
        const avail = sourcesFor(commodity)
        const src = source && (avail as string[]).includes(source)
            ? source
            : (avail.length ? avail[0] : 'none')
        setParam({ item: commodity, src })
        setFindOpen(false)
        loadSeries(commodity, src)
    }, [sourcesFor, loadSeries, setParam])

    // ---- what renders on load -----------------------------------------------
    // Resolution order: an explicit ?item= (or the legacy ?commodity=), then the
    // default item, then — only if neither resolves — the first browsable item
    // with a monthly-or-finer source. The page must never reach a state where
    // nothing is charted.
    useEffect(() => {
        if (loading || selectedCommodity) return
        const want = (searchParams.get('item') || searchParams.get('commodity') || '')
            .trim().toLowerCase()
        const wantSrc = searchParams.get('src') || undefined

        const pick = (slug: string, src?: string) => {
            if (coverage[slug] && sourcesFor(slug).length > 0) { selectCommodity(slug, src); return true }
            if (AV_HISTORY_COMMODITIES.has(slug)) { loadSeries(slug, 'av'); setSelectedCommodity(slug); return true }
            return false
        }
        if (want && pick(want, wantSrc)) return
        if (pick(DEFAULT_ITEM, DEFAULT_SOURCE)) return
        const firstMonthly = Object.keys(coverage)
            .filter(s => sourcesFor(s).length > 0)
            .find(s => hasSeasonalSignal(bestFreqFor(s)))
        if (firstMonthly) pick(firstMonthly)
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [loading, coverage, searchParams])

    // The detail rail follows the selected item.
    useEffect(() => {
        if (!selectedCommodity) return
        let cancelled = false
        setDetail(null)
        api.getPriceDetail(selectedCommodity)
            .then(res => { if (!cancelled) setDetail(res.data as PriceDetail) })
            // A 404 or a backend without the endpoint is not a page error: the
            // rail falls back to what the coverage payload already carries.
            .catch(() => { if (!cancelled) setDetail(null) })
        return () => { cancelled = true }
    }, [selectedCommodity])

    // ---- the browsable universe ---------------------------------------------
    const allSlugs = useMemo(() => Object.keys(coverage), [coverage])
    const items = useMemo<ExplorerItem[]>(() => allSlugs
        .filter(slug => sourcesFor(slug).length > 0)
        .map(slug => ({
            slug,
            label: displayNames[slug] ?? slug,
            category: classifyCommodity(slug, displayNames[slug]),
            bestFreq: bestFreqFor(slug),
        })), [allSlugs, displayNames, sourcesFor, bestFreqFor])
    const excludedSingleYear = allSlugs.length - items.length

    // Frequency is a FIRST-CLASS FILTER, not a badge alone. Annual sources are
    // stored and reachable, but off by default: "annual is too infrequent for
    // my chef friend to really dive in."
    const freqExcluded = useMemo(
        () => items.filter(i => !freqFilter.has(i.bestFreq)).length, [items, freqFilter])

    const filteredCommodities = useMemo(() => items
        .filter(c => {
            if (!freqFilter.has(c.bestFreq)) return false
            const needle = searchTerm.trim().toLowerCase()
            const matchesSearch = !needle
                || c.slug.includes(needle)
                || c.label.toLowerCase().includes(needle)
            if (selectedCategory === 'all') return matchesSearch
            return matchesSearch && c.category === selectedCategory
        })
        .sort((a, b) => {
            // The item currently on screen always sorts first, so the reader can
            // see what they are looking at without hunting a 60-row list. Then
            // finer frequency, then coverage breadth, then name.
            if (a.slug === selectedCommodity) return -1
            if (b.slug === selectedCommodity) return 1
            const rank: Record<Frequency, number> = { daily: 0, weekly: 1, monthly: 2, annual: 3 }
            if (rank[a.bestFreq] !== rank[b.bestFreq]) return rank[a.bestFreq] - rank[b.bestFreq]
            const an = sourcesFor(a.slug).length
            const bn = sourcesFor(b.slug).length
            return an !== bn ? bn - an : a.label.localeCompare(b.label)
        }), [items, searchTerm, selectedCategory, freqFilter, sourcesFor, selectedCommodity])

    // ---- real, server-side search across the underlying price tables --------
    //
    // Before Tier 0 the search box was a substring filter over the already
    // truncated in-memory list, so typing "tomato" returned "Commodities (0)"
    // with no explanation while 552 monthly BLS tomato observations sat in the
    // database. /api/prices/search has always covered retail_prices.food_item
    // (and the WASDE / global tables); api.searchPrices was defined in the
    // frontend and never called. It is called now.
    useEffect(() => {
        const needle = searchTerm.trim()
        if (needle.length < 2) { setSearchHits(null); setSearching(false); return }
        let cancelled = false
        setSearching(true)
        const handle = window.setTimeout(() => {
            api.searchPrices(needle, 'wasde,global,retail', { limit: '400' })
                .then(res => {
                    if (cancelled) return
                    const buckets = res.data?.results ?? {}
                    const acc = new Map<string, SearchHit>()
                    const add = (name: unknown, source: string, date?: unknown) => {
                        if (!name) return
                        const key = `${source}::${String(name)}`
                        const hit = acc.get(key)
                            ?? { name: String(name), source, observations: 0 }
                        hit.observations += 1
                        const d = date ? String(date).slice(0, 10) : undefined
                        if (d && (!hit.latest || d > hit.latest)) hit.latest = d
                        acc.set(key, hit)
                    }
                    for (const r of buckets.retail ?? []) add(r.food_item, 'BLS US retail', r.date)
                    for (const r of buckets.global ?? []) add(r.commodity, 'Global spot', r.date)
                    for (const r of buckets.wasde ?? []) add(r.commodity, 'USDA', r.year)
                    const bySlug = new Map(items.map(i => [i.label.toLowerCase(), i.slug]))
                    const hits = [...acc.values()].map(h => ({
                        ...h,
                        slug: bySlug.get(h.name.toLowerCase())
                            ?? (coverage[h.name.toLowerCase()] ? h.name.toLowerCase() : undefined),
                    }))
                    hits.sort((a, b) => b.observations - a.observations)
                    setSearchHits(hits.slice(0, 25))
                })
                .catch(() => { if (!cancelled) setSearchHits([]) })
                .finally(() => { if (!cancelled) setSearching(false) })
        }, 300)
        return () => { cancelled = true; window.clearTimeout(handle) }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchTerm, items])

    const spanLabel = (name: string): string | null => {
        const cov = covFor(name)
        const best = SOURCE_ORDER.map(s => cov[s]).find(Boolean)
        if (!best) return null
        const y0 = best.start?.slice(0, 4)
        const y1 = best.end?.slice(0, 4)
        return y0 && y1 ? `${y0}–${y1}` : null
    }

    // =======================================================================
    // THE SERIES PIPELINE
    //
    // raw -> kitchen unit -> real terms -> transform -> range clip
    //
    // The transform runs BEFORE the range clip so a 1-year view of a YoY series
    // still has the prior year available to difference against; clipping first
    // would silently drop the first twelve points of every short view.
    // =======================================================================
    const rawRows: Obs[] = useMemo(() => series?.data ?? [], [series])
    const nativeUnit = series?.unit || null
    const freq = selectedCommodity && selectedSource !== 'none'
        ? freqOf(selectedCommodity, selectedSource as SourceKey)
        : 'annual'

    const unitOptions: UnitOption[] = useMemo(
        () => convertibleUnits(nativeUnit, selectedCommodity ?? undefined),
        [nativeUnit, selectedCommodity])
    const unit = unitOptions[Math.min(unitIdx, unitOptions.length - 1)] ?? unitOptions[0]

    const converted = useMemo(() => convert(rawRows, unit?.factor ?? 1), [rawRows, unit])
    const realResult = useMemo<RealResult>(
        () => (real
            ? toRealTerms(converted, deflator)
            : { rows: converted, dropped: 0, carried: 0, deflatorEnd: null, baseLabel: null }),
        [real, converted, deflator])
    const transformed = useMemo(
        () => applyTransform(realResult.rows, transform), [realResult.rows, transform])
    const logged = useMemo(
        () => (transform === 'log' ? logSafe(transformed) : { rows: transformed, dropped: 0 }),
        [transform, transformed])
    const chartData = useMemo(() => clipToRange(logged.rows, range), [logged.rows, range])

    // The y-axis label. This used to read the literal word "Value" whenever a
    // publisher shipped no unit string (`series?.unit || 'Value'`) — an axis
    // that tells the reader nothing. It now always names either a real unit or
    // what the transform produced.
    const axisUnit = transformedUnit(
        transform, unit?.label || nativeUnit || 'Price (unit not published)')

    // Seasonality is computed over the FULL converted history, not the clipped
    // range: a seasonal normal drawn from a 1-year window is not a normal.
    const season = useMemo(
        () => (hasSeasonalSignal(freq) ? seasonality(realResult.rows) : null),
        [freq, realResult.rows])

    const stats = useMemo(() => deltas(realResult.rows, freq), [realResult.rows, freq])
    const availableSources = selectedCommodity ? sourcesFor(selectedCommodity) : []
    const itemLabel = selectedCommodity
        ? (displayNames[selectedCommodity] ?? detail?.label ?? selectedCommodity)
        : ''

    const pinKey = selectedCommodity ? `${selectedCommodity}:${selectedSource}` : ''
    const isPinned = pinned.includes(pinKey)
    const togglePin = () => {
        const next = isPinned ? pinned.filter(p => p !== pinKey) : [...pinned, pinKey].slice(0, 6)
        setParam({ pin: next.join(',') })
    }

    const csvRows = chartData.map(r => ({
        date: r.date, year: r.year, value: r.price, unit: axisUnit,
        item: itemLabel, source: SOURCE_LABELS[selectedSource] ?? selectedSource,
    }))
    const fileStem = `foodberg_${selectedCommodity ?? 'series'}_${selectedSource}${real ? '_real' : ''}`

    // -----------------------------------------------------------------------

    const findColumn = (
        <div className="card">
            {/* Search — site-wide and real: it queries every price table, not
                the in-memory list. */}
            <div className="relative mb-3">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ark-fg-dim" />
                <input
                    type="text"
                    aria-label="Search every price series"
                    placeholder="Search every series — “tomato”, “bacon”, “lettuce”…"
                    value={searchTerm}
                    onChange={(e) => setParam({ q: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 bg-ark-tag border border-ark-line rounded-lg text-ark-fg placeholder-ark-fg-dim focus:outline-none focus:border-emerald-500"
                />
            </div>
            {searchTerm.trim().length >= 2 && (
                <div className="mb-3 text-xs text-ark-fg-dim">
                    {searching
                        ? 'Searching the price tables…'
                        : searchHits === null
                            ? null
                            : searchHits.length === 0
                                ? `No series in the database matches “${searchTerm.trim()}”. This is a real result, not a truncated list — the search runs against every price table.`
                                : `${filteredCommodities.length} browsable · ${searchHits.length} matching series in the underlying data`}
                </div>
            )}

            {/* Kitchen categories */}
            <div className="mb-3">
                <div className="text-[11px] font-semibold uppercase tracking-wide text-ark-fg-dim mb-1.5">Kitchen category</div>
                <div className="flex gap-1.5 flex-wrap">
                    {(['all', ...KITCHEN_CATEGORIES] as const).map(cat => (
                        <button
                            key={cat}
                            onClick={() => setParam({ cat: cat === 'all' ? null : cat })}
                            className={`px-2 py-1 rounded text-xs font-medium transition-colors ${selectedCategory === cat
                                ? 'bg-emerald-600 text-white'
                                : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'}`}
                        >
                            {cat === 'all' ? 'All' : cat}
                        </button>
                    ))}
                </div>
            </div>

            {/* Frequency filter — first-class, always visible */}
            <div className="mb-4">
                <div className="text-[11px] font-semibold uppercase tracking-wide text-ark-fg-dim mb-1.5">
                    Update frequency
                </div>
                <div className="flex gap-1.5 flex-wrap">
                    {FREQUENCIES.map(f => {
                        const on = freqFilter.has(f)
                        return (
                            <button
                                key={f}
                                aria-pressed={on}
                                onClick={() => {
                                    const next = new Set(freqFilter)
                                    if (on) next.delete(f); else next.add(f)
                                    if (!next.size) return   // never filter to nothing
                                    setParam({ freq: FREQUENCIES.filter(x => next.has(x)).join(',') })
                                }}
                                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${on
                                    ? 'bg-emerald-600 text-white'
                                    : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'}`}
                            >
                                {on ? '▣' : '☐'} {FREQUENCY_LABEL[f]}
                            </button>
                        )
                    })}
                </div>
                {freqExcluded > 0 && (
                    <p className="text-[11px] text-ark-fg-dim mt-1.5">
                        {freqExcluded} item{freqExcluded === 1 ? '' : 's'} hidden by this filter.
                        Annual sources are stored and searchable — they are just off by default,
                        because an annual price is too coarse to cook against.
                    </p>
                )}
                {/* Do not let a filter imply coverage the explorer does not have.
                    USDA AMS publishes DAILY, and 1.67M of those rows are loaded —
                    but they are line items (variety x package x grade x origin x
                    city), not one series per commodity, so they are browsed on
                    /wholesale rather than charted here. Saying so beats a
                    "Daily" checkbox that silently matches nothing. */}
                {freqFilter.has('daily') && !items.some(i => i.bestFreq === 'daily') && (
                    <p className="text-[11px] text-ark-fg-dim mt-1.5">
                        No daily <em>series</em> here yet. Daily USDA AMS terminal-market prices are
                        loaded and live, but they are individual wholesale line items rather than one
                        series per ingredient —{' '}
                        <Link to="/wholesale" className="text-emerald-400 hover:text-emerald-300">
                            browse them on Wholesale
                        </Link>. Each item's latest wholesale range also appears in its detail rail.
                    </p>
                )}
            </div>

            {/* The list */}
            <h2 className="text-sm font-semibold text-ark-fg mb-2 flex items-center">
                <BarChart3 className="w-4 h-4 mr-2 text-emerald-400" />
                Commodities ({filteredCommodities.length})
            </h2>
            {loading ? (
                <div className="text-center py-8">
                    <div className="animate-spin w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full mx-auto"></div>
                    <p className="text-ark-fg-dim mt-2">Loading commodities…</p>
                </div>
            ) : (
                <div className="space-y-1.5 max-h-[520px] overflow-y-auto">
                    {filteredCommodities.length === 0 && (
                        <p className="text-sm text-ark-fg-dim py-4">
                            Nothing matches{searchTerm.trim() ? ` “${searchTerm.trim()}”` : ''} in this
                            category at the selected frequencies.
                        </p>
                    )}
                    {filteredCommodities.map(item => {
                        const srcs = sourcesFor(item.slug)
                        const nSrc = srcs.length
                        const span = spanLabel(item.slug)
                        const isDisplayName = item.label !== item.slug
                        // Best (freshest) liveness across the item's sources — an
                        // item is only flagged when EVERY source it has is stale.
                        const best = srcs
                            .map(s => covFor(item.slug)[s]?.liveness)
                            .filter(Boolean) as Liveness[]
                        const worstFirst = ['live', 'stale', 'unknown', 'discontinued']
                        const live = best.slice().sort(
                            (a, b) => worstFirst.indexOf(a.status) - worstFirst.indexOf(b.status))[0]
                        return (
                            <button
                                key={item.slug}
                                onClick={() => selectCommodity(item.slug)}
                                className={`w-full text-left p-2.5 rounded-lg transition-colors ${selectedCommodity === item.slug
                                    ? 'bg-emerald-600/20 border border-emerald-500/50'
                                    : 'bg-ark-bg-soft hover:bg-ark-tag border border-transparent'}`}
                            >
                                <div className="flex justify-between items-center gap-2">
                                    <span className={`font-medium text-sm text-ark-fg${isDisplayName ? '' : ' capitalize'}`}>
                                        {item.label}
                                    </span>
                                    <FreqBadge freq={item.bestFreq} />
                                </div>
                                <div className="text-[11px] text-ark-fg-dim mt-0.5">
                                    {span ? `${span}` : 'Multi-year'} · {nSrc} source{nSrc > 1 ? 's' : ''} · {item.category}
                                </div>
                                {live && live.status !== 'live' && (
                                    <div className={`inline-block mt-1 text-[10px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded ${LIVENESS_STYLE[live.status]}`}>
                                        {live.status}
                                    </div>
                                )}
                            </button>
                        )
                    })}
                </div>
            )}

            {/* Real server-side search results (/api/prices/search) — shown so a
                term that matches data the browsable list does not carry is still
                visible, with an honest observation count, instead of a silent zero. */}
            {searchHits && searchHits.length > 0 && (
                <div className="mt-4 pt-4 border-t border-ark-line">
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-ark-fg-dim mb-2">
                        Matching series in the data ({searchHits.length})
                    </h3>
                    <div className="space-y-1 max-h-56 overflow-y-auto">
                        {searchHits.map(hit => (
                            <button
                                key={`${hit.source}-${hit.name}`}
                                type="button"
                                disabled={!hit.slug}
                                onClick={() => hit.slug && selectCommodity(hit.slug)}
                                className={`w-full text-left px-2 py-1.5 rounded text-xs ${hit.slug
                                    ? 'hover:bg-ark-tag text-ark-fg cursor-pointer'
                                    : 'text-ark-fg-dim cursor-default'}`}
                            >
                                <span className="font-medium">{hit.name}</span>
                                <span className="text-ark-fg-dim">
                                    {' '}· {hit.source}
                                    {hit.latest ? ` · latest ${hit.latest}` : ''}
                                    {hit.slug ? '' : ' · chart not available'}
                                </span>
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )

    return (
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
            {/* Title block — deliberately short. The chart is the product; the
                explanation lives under it, not above it. */}
            <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-ark-fg">Food prices, as published</h1>
                    <p className="text-sm text-ark-fg-dim mt-1 max-w-3xl">
                        Daily wholesale, monthly retail and long-run farm-gate prices from USDA AMS, BLS,
                        the World Bank and USDA NASS — in kitchen units, with seasonality. Nothing is
                        interpolated or extrapolated.
                    </p>
                </div>
                <button
                    type="button"
                    onClick={() => setFindOpen(true)}
                    className="lg:hidden btn-secondary text-sm px-4 py-2"
                >
                    <Search className="w-4 h-4 inline mr-1" /> Find a price
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[minmax(260px,320px)_1fr] gap-6">
                {/* FIND — a column on desktop, a bottom sheet on mobile. */}
                <aside className="hidden lg:block">{findColumn}</aside>
                {findOpen && (
                    <div className="lg:hidden fixed inset-0 z-50 bg-black/60 flex items-end" onClick={() => setFindOpen(false)}>
                        <div
                            className="w-full max-h-[85vh] overflow-y-auto bg-ark-bg rounded-t-2xl p-4"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="flex justify-between items-center mb-3">
                                <h2 className="font-semibold text-ark-fg">Find a price</h2>
                                <button onClick={() => setFindOpen(false)} aria-label="Close" className="p-1">
                                    <X className="w-5 h-5 text-ark-fg-dim" />
                                </button>
                            </div>
                            {findColumn}
                        </div>
                    </div>
                )}

                {/* CHART + RAIL */}
                <main className="min-w-0 space-y-6">
                    <div className="card">
                        {selectedCommodity && series ? (
                            <>
                                {/* Headline: a price, a unit, and a change — never an index. */}
                                <div className="flex flex-wrap justify-between items-start gap-3 mb-3">
                                    <div>
                                        <h2 className={`text-xl font-semibold text-ark-fg${displayNames[selectedCommodity] ? '' : ' capitalize'}`}>
                                            {itemLabel}
                                        </h2>
                                        {stats.latest && (
                                            <div className="flex items-baseline gap-3 flex-wrap mt-1">
                                                <span className="text-4xl font-bold text-emerald-400">
                                                    {fmtPrice(stats.latest.price, transform === 'none' ? unit?.label : undefined)}
                                                </span>
                                                <span className="text-sm text-ark-fg-dim">
                                                    {fmtMonth(stats.latest.date)}
                                                    {unit && !unit.native ? ` · converted from ${nativeUnit}` : ''}
                                                    {real && realResult.baseLabel ? ` · constant ${realResult.baseLabel} dollars` : ''}
                                                </span>
                                                {stats.vsYearAgo && (
                                                    <span className={`text-sm font-semibold ${stats.vsYearAgo.pct >= 0 ? 'text-rose-700 dark:text-rose-300' : 'text-emerald-700 dark:text-emerald-300'}`}>
                                                        {fmtPct(stats.vsYearAgo.pct)} vs a year ago
                                                    </span>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <button
                                            type="button"
                                            onClick={togglePin}
                                            className={`ark-btn ark-btn-sm ${isPinned ? '' : 'ark-btn-ghost'}`}
                                            title="Pin this series to the comparison tray"
                                        >
                                            <Pin className="w-3.5 h-3.5 inline mr-1" />
                                            {isPinned ? 'Pinned' : 'Compare'}
                                        </button>
                                        {/* The commodity-detail route is built on the USDA
                                            WASDE universe; BLS-AP-only items have no page
                                            there, so the link is not offered for them. */}
                                        {!displayNames[selectedCommodity] && (
                                            <Link
                                                to={`/commodity/${selectedCommodity}`}
                                                className="text-sm text-emerald-400 hover:text-emerald-300"
                                            >
                                                Details →
                                            </Link>
                                        )}
                                    </div>
                                </div>

                                {/* ---- THE CONTROL CLUSTER — always visible ---------- */}
                                <div className="flex flex-wrap items-center gap-2 mb-3 pb-3 border-b border-ark-line">
                                    {/* Unit: the primary control, kitchen units first. */}
                                    <label className="flex items-center gap-1.5 text-xs text-ark-fg-dim">
                                        <span className="sr-only sm:not-sr-only">Unit</span>
                                        <select
                                            aria-label="Unit"
                                            value={String(Math.min(unitIdx, unitOptions.length - 1))}
                                            onChange={e => setParam({ u: e.target.value })}
                                            disabled={unitOptions.length < 2}
                                            className="bg-ark-tag border border-ark-line rounded px-2 py-1 text-ark-fg text-xs disabled:opacity-60"
                                        >
                                            {unitOptions.map((o, i) => (
                                                <option key={o.label} value={String(i)}>
                                                    {o.label}{o.native ? ' (as published)' : ''}
                                                </option>
                                            ))}
                                        </select>
                                    </label>

                                    {/* Nominal / real — GDP deflator, never CPI. */}
                                    <div className="inline-flex rounded border border-ark-line overflow-hidden">
                                        {(['0', '1'] as const).map(v => (
                                            <button
                                                key={v}
                                                onClick={() => setParam({ real: v === '0' ? null : '1' })}
                                                disabled={v === '1' && !deflator}
                                                title={v === '1' && !deflator
                                                    ? 'The GDP deflator has not been ingested, so real terms are unavailable.'
                                                    : undefined}
                                                className={`px-2.5 py-1 text-xs font-medium disabled:opacity-40 ${(real ? '1' : '0') === v
                                                    ? 'bg-emerald-600 text-white' : 'bg-ark-tag text-ark-fg-dim'}`}
                                            >
                                                {v === '0' ? 'Nominal' : 'Real'}
                                            </button>
                                        ))}
                                    </div>

                                    {/* Transform cluster (ark-chart.js parity). */}
                                    <select
                                        aria-label="Transform"
                                        value={transform}
                                        onChange={e => setParam({ t: e.target.value === 'none' ? null : e.target.value })}
                                        className="bg-ark-tag border border-ark-line rounded px-2 py-1 text-ark-fg text-xs"
                                    >
                                        {TRANSFORMS.map(tr => (
                                            <option key={tr.key} value={tr.key} title={tr.hint}>{tr.label}</option>
                                        ))}
                                    </select>

                                    {/* Range */}
                                    <div className="inline-flex rounded border border-ark-line overflow-hidden">
                                        {RANGES.map(r => (
                                            <button
                                                key={r.key}
                                                onClick={() => setParam({ r: r.key === 'max' ? null : r.key })}
                                                className={`px-2 py-1 text-xs font-medium ${range === r.key
                                                    ? 'bg-emerald-600 text-white' : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'}`}
                                            >
                                                {r.label}
                                            </button>
                                        ))}
                                    </div>

                                    <div className="ml-auto">
                                        <ArkDownloads
                                            rows={csvRows}
                                            filename={fileStem}
                                            label={null}
                                            hrefs={{
                                                xlsx: selectedSource === 'retail' ? '/api/download/retail_prices.xlsx' : undefined,
                                                parquet: selectedSource === 'retail' ? '/api/download/retail_prices.parquet' : undefined,
                                            }}
                                        />
                                    </div>
                                </div>

                                {/* Source tabs, each carrying its own frequency badge and
                                    last-real-observation, so a chef can see at a glance
                                    which source is daily and which stopped in 2017. */}
                                {availableSources.length > 0 && (
                                    <div className="flex gap-2 mb-3 flex-wrap">
                                        {availableSources.map((s) => {
                                            const c = covFor(selectedCommodity)[s]
                                            const f = freqOf(selectedCommodity, s)
                                            return (
                                                <button
                                                    key={s}
                                                    onClick={() => selectCommodity(selectedCommodity, s)}
                                                    className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${selectedSource === s
                                                        ? 'bg-emerald-600 text-white'
                                                        : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'}`}
                                                >
                                                    {SOURCE_LABELS[s]}
                                                    <FreqBadge freq={f} />
                                                    <span className="opacity-70">
                                                        {c?.liveness?.last_real_observation?.slice(0, 7) ?? ''}
                                                    </span>
                                                </button>
                                            )
                                        })}
                                    </div>
                                )}

                                {/* Never present a series the publisher stopped
                                    updating as if it were current (S5). */}
                                {(() => {
                                    const note = livenessNote(
                                        covFor(selectedCommodity)[selectedSource as SourceKey]?.liveness)
                                    if (!note) return null
                                    return (
                                        <div className="mb-3 px-3 py-2 rounded-lg border border-amber-500/50 bg-amber-50 text-sm text-amber-900 dark:bg-amber-900/20 dark:text-amber-200">
                                            {note}. The history below is real; the series is not current.
                                        </div>
                                    )
                                })()}

                                {/* Honest notices about what the current view drops. */}
                                {real && realResult.unavailable && (
                                    <div className="mb-3 px-3 py-2 rounded-lg border border-amber-500/50 bg-amber-50 text-sm text-amber-900 dark:bg-amber-900/20 dark:text-amber-200">
                                        {realResult.unavailable}
                                    </div>
                                )}
                                {real && (realResult.dropped > 0 || realResult.carried > 0) && (
                                    <div className="mb-3 px-3 py-2 rounded-lg border border-ark-line bg-ark-tag text-xs text-ark-fg-dim space-y-1">
                                        {realResult.dropped > 0 && (
                                            <div>
                                                {realResult.dropped.toLocaleString()} observation
                                                {realResult.dropped === 1 ? '' : 's'} pre-date the GDP deflator
                                                ({deflator?.coverage?.start?.slice(0, 4) ?? '1947'}→) and cannot
                                                be put in constant dollars, so they are not plotted here.
                                                Switch to Nominal to see the full history.
                                            </div>
                                        )}
                                        {realResult.carried > 0 && (
                                            <div>
                                                The {realResult.carried} most recent observation
                                                {realResult.carried === 1 ? ' is' : 's are'} newer than the last
                                                published deflator quarter ({realResult.deflatorEnd}), because the
                                                BEA publishes it quarterly and in arrears. They are shown at that
                                                quarter's price level rather than dropped — so the latest price is
                                                still here, with at most one quarter of inflation unaccounted for.
                                            </div>
                                        )}
                                    </div>
                                )}
                                {transform === 'log' && logged.dropped > 0 && (
                                    <div className="mb-3 px-3 py-2 rounded-lg border border-ark-line bg-ark-tag text-xs text-ark-fg-dim">
                                        {logged.dropped} non-positive observation
                                        {logged.dropped === 1 ? '' : 's'} cannot be drawn on a log axis.
                                    </div>
                                )}

                                {/* ---- THE CHART ------------------------------------- */}
                                {series.has_history && chartData.length > 1 ? (
                                    <div className="h-[400px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={chartData} margin={{ left: 12, right: 8, bottom: 8 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke={t.gridStroke} />
                                                {/* THE FIX: this axis used to be dataKey="year",
                                                    which plotted a 552-point monthly series against
                                                    a year axis and threw every month away. The
                                                    months are the chef's signal. */}
                                                <XAxis
                                                    dataKey="date"
                                                    stroke={t.axisStroke}
                                                    tick={{ fill: t.dim, fontSize: 11 }}
                                                    minTickGap={48}
                                                    tickFormatter={(d: string) =>
                                                        freq === 'annual' ? String(d).slice(0, 4) : fmtMonth(d)}
                                                />
                                                <YAxis
                                                    stroke={t.axisStroke}
                                                    tick={{ fill: t.dim, fontSize: 11 }}
                                                    scale={transform === 'log' ? 'log' : 'auto'}
                                                    domain={transform === 'log' ? ['auto', 'auto'] : undefined}
                                                    width={72}
                                                    tickFormatter={(value: number) => value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                                                    label={{ value: axisUnit, angle: -90, position: 'insideLeft', fill: t.dim, fontSize: 11, style: { textAnchor: 'middle' } }}
                                                />
                                                <Tooltip
                                                    contentStyle={t.tooltip}
                                                    labelStyle={{ color: t.fg }}
                                                    labelFormatter={(d: string) => fmtMonth(String(d))}
                                                    formatter={(value: number) => [fmtPrice(value, transform === 'none' ? unit?.label : undefined), axisUnit]}
                                                />
                                                {/* Legend BELOW the plot — Universal Graph Contract. */}
                                                <Legend verticalAlign="bottom" height={28} wrapperStyle={{ color: t.dim, fontSize: 12 }} />
                                                <Line
                                                    type="monotone"
                                                    dataKey="price"
                                                    name={`${itemLabel} — ${SOURCE_LABELS[selectedSource] ?? selectedSource}`}
                                                    stroke={t.accent}
                                                    strokeWidth={2}
                                                    dot={false}
                                                    activeDot={{ r: 5, fill: t.accent }}
                                                />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                ) : (
                                    /* Honest single-point view: a stat card, not a fake line. */
                                    <div className="h-[400px] flex flex-col items-center justify-center text-center">
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
                                        unit: axisUnit,
                                        dateRange: chartData.length
                                            ? `${chartData[0].date.slice(0, 7)} → ${chartData[chartData.length - 1].date.slice(0, 7)}`
                                            : null,
                                        points: chartData.length,
                                        latestLabel: 'Latest',
                                        latestValue: stats.latest
                                            ? `${fmtPrice(stats.latest.price, transform === 'none' ? unit?.label : undefined)} (${stats.latest.date.slice(0, 7)})`
                                            : null,
                                        note: unit && !unit.native
                                            ? `Converted from the publisher's ${nativeUnit}. The published series is unchanged; the conversion is exact and applied in the browser.`
                                            : null,
                                    }}
                                />
                            </>
                        ) : (
                            <div className="h-[420px] flex items-center justify-center text-ark-fg-dim">
                                Loading a price…
                            </div>
                        )}
                    </div>

                    {/* ---- SEASONAL BAND — on by default for monthly-or-finer -----
                        The chef's core question. This data has been in the database
                        the whole time and was destroyed at the presentation layer:
                        the old chart plotted monthly series against a year axis and
                        HistoricalTrends averaged months into annual points. It is
                        pure compute — nothing was acquired to build this. */}
                    {season && (
                        <div className="card">
                            <div className="flex flex-wrap items-baseline justify-between gap-2 mb-1">
                                <h3 className="text-lg font-semibold text-ark-fg">
                                    When is it cheap? <span className="text-ark-fg-dim font-normal">{itemLabel}</span>
                                </h3>
                                <span className="text-xs text-ark-fg-dim">
                                    Month-of-year profile · {season.yearsUsed} years ({season.yearFrom}–{season.yearTo})
                                </span>
                            </div>
                            <p className="text-sm text-ark-fg-dim mb-3">
                                Cheapest in <strong className="text-emerald-400">{season.cheapest?.name}</strong>
                                {' '}({fmtPrice(season.cheapest?.median, unit?.label)}), dearest in{' '}
                                <strong className="text-rose-700 dark:text-rose-300">{season.dearest?.name}</strong>
                                {' '}({fmtPrice(season.dearest?.median, unit?.label)})
                                {season.swingPct != null && <> — a {season.swingPct.toFixed(0)}% seasonal swing</>}.
                                {season.currentPercentile != null && season.currentMonth && (
                                    <> The latest {season.currentMonth.name} price sits at the{' '}
                                        {season.currentPercentile.toFixed(0)}th percentile of{' '}
                                        {season.currentMonth.name}s in this window.</>
                                )}
                            </p>
                            <div className="h-[300px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <ComposedChart
                                        data={season.months.map(m => ({
                                            name: m.name,
                                            band: [m.p25, m.p75] as [number, number],
                                            median: m.median,
                                            latestYear: m.latestYear ?? null,
                                        }))}
                                        margin={{ left: 12, right: 8, bottom: 8 }}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" stroke={t.gridStroke} />
                                        <XAxis dataKey="name" stroke={t.axisStroke} tick={{ fill: t.dim, fontSize: 11 }} />
                                        <YAxis
                                            stroke={t.axisStroke}
                                            tick={{ fill: t.dim, fontSize: 11 }}
                                            width={72}
                                            tickFormatter={(v: number) => v.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                                            label={{ value: unit?.label ?? '', angle: -90, position: 'insideLeft', fill: t.dim, fontSize: 11, style: { textAnchor: 'middle' } }}
                                        />
                                        <Tooltip
                                            contentStyle={t.tooltip}
                                            labelStyle={{ color: t.fg }}
                                            formatter={(v: number | [number, number], n: string) =>
                                                Array.isArray(v)
                                                    ? [`${fmtPrice(v[0], unit?.label)} – ${fmtPrice(v[1], unit?.label)}`, n]
                                                    : [fmtPrice(v as number, unit?.label), n]}
                                        />
                                        <Legend verticalAlign="bottom" height={28} wrapperStyle={{ color: t.dim, fontSize: 12 }} />
                                        <Area
                                            dataKey="band"
                                            name="Typical range (25th–75th percentile)"
                                            stroke="none"
                                            fill={t.accent}
                                            fillOpacity={0.18}
                                        />
                                        <Line
                                            dataKey="median"
                                            name={`Seasonal normal (median, ${season.yearFrom}–${season.yearTo})`}
                                            stroke={t.accent} strokeWidth={2} dot={false}
                                        />
                                        <Line
                                            dataKey="latestYear"
                                            name={`${season.yearTo} actual`}
                                            stroke={t.colorway[2]} strokeWidth={2}
                                            strokeDasharray="4 3" dot={{ r: 2 }} connectNulls
                                        />
                                    </ComposedChart>
                                </ResponsiveContainer>
                            </div>
                            <ScrollableDataTable
                                title="Month-of-year statistics"
                                rows={season.months.map(m => ({
                                    month: m.name, years: m.n,
                                    median: m.median, p25: m.p25, p75: m.p75,
                                    min: m.min, max: m.max,
                                    vs_typical: `${(m.indexed - 100).toFixed(1)}%`,
                                }))}
                                columns={[
                                    { key: 'month', label: 'Month' },
                                    { key: 'years', label: 'Years', numeric: true },
                                    { key: 'median', label: `Median (${unit?.label ?? ''})`, numeric: true },
                                    { key: 'p25', label: '25th pct', numeric: true },
                                    { key: 'p75', label: '75th pct', numeric: true },
                                    { key: 'min', label: 'Min', numeric: true },
                                    { key: 'max', label: 'Max', numeric: true },
                                    { key: 'vs_typical', label: 'vs typical month' },
                                ]}
                                filename={`${fileStem}_seasonal`}
                            />
                            <p className="text-xs text-ark-fg-dim mt-3">
                                Computed in the browser from the {realResult.rows.length.toLocaleString()}
                                {' '}observations above. A month is only shown when at least three years
                                contributed to it. <Link to={`/seasons?item=${selectedCommodity}&source=${selectedSource}`} className="text-emerald-400 hover:text-emerald-300">Full seasonality view →</Link>
                            </p>
                        </div>
                    )}
                    {!season && hasSeasonalSignal(freq) && series?.has_history && (
                        <div className="card text-sm text-ark-fg-dim">
                            <strong className="text-ark-fg">No seasonal profile.</strong> This series is
                            monthly, but it does not carry enough complete months across enough years to
                            build an honest month-of-year distribution (at least three years per month,
                            and at least six qualifying months). Rather than draw a half-empty band, the
                            page says so.
                        </div>
                    )}

                    {/* ---- THE DETAIL RAIL — the "maximum options" surface -------- */}
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                        {/* Now / vs last period / vs last year / vs 5-yr average */}
                        <RailBlock title="Now, and against what">
                            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                                <dt className="text-ark-fg-dim">Latest</dt>
                                <dd className="text-ark-fg font-medium text-right">
                                    {stats.latest ? `${fmtPrice(stats.latest.price, unit?.label)} · ${stats.latest.date.slice(0, 7)}` : '—'}
                                </dd>
                                <dt className="text-ark-fg-dim">{stats.vsPrevious?.label ?? 'vs previous'}</dt>
                                <dd className={`text-right font-medium ${(stats.vsPrevious?.pct ?? 0) >= 0 ? 'text-rose-700 dark:text-rose-300' : 'text-emerald-700 dark:text-emerald-300'}`}>
                                    {fmtPct(stats.vsPrevious?.pct)}
                                </dd>
                                <dt className="text-ark-fg-dim">vs a year ago</dt>
                                <dd className={`text-right font-medium ${(stats.vsYearAgo?.pct ?? 0) >= 0 ? 'text-rose-700 dark:text-rose-300' : 'text-emerald-700 dark:text-emerald-300'}`}>
                                    {fmtPct(stats.vsYearAgo?.pct)}
                                    {stats.vsYearAgo && (
                                        <span className="text-ark-fg-dim font-normal"> (from {fmtPrice(stats.vsYearAgo.from.price, unit?.label)})</span>
                                    )}
                                </dd>
                                <dt className="text-ark-fg-dim">
                                    vs {stats.vsFiveYearAvg ? `${stats.vsFiveYearAvg.years}-yr` : '5-yr'} average
                                </dt>
                                <dd className={`text-right font-medium ${(stats.vsFiveYearAvg?.pct ?? 0) >= 0 ? 'text-rose-700 dark:text-rose-300' : 'text-emerald-700 dark:text-emerald-300'}`}>
                                    {fmtPct(stats.vsFiveYearAvg?.pct)}
                                    {stats.vsFiveYearAvg && (
                                        <span className="text-ark-fg-dim font-normal"> ({fmtPrice(stats.vsFiveYearAvg.avg, unit?.label)})</span>
                                    )}
                                </dd>
                                <dt className="text-ark-fg-dim">Range on record</dt>
                                <dd className="text-ark-fg text-right">
                                    {stats.allTimeLow && stats.allTimeHigh
                                        ? `${fmtPrice(stats.allTimeLow.price, unit?.label)} (${stats.allTimeLow.date.slice(0, 7)}) – ${fmtPrice(stats.allTimeHigh.price, unit?.label)} (${stats.allTimeHigh.date.slice(0, 7)})`
                                        : '—'}
                                </dd>
                            </dl>
                            {real && (
                                <p className="text-[11px] text-ark-fg-dim mt-2">
                                    In constant {realResult.baseLabel} dollars, deflated by the GDP implicit
                                    price deflator — never CPI, which contains food prices and would make
                                    the comparison circular.
                                </p>
                            )}
                        </RailBlock>

                        {/* Every source carrying this item */}
                        <RailBlock
                            title="Every source carrying this item"
                            badge={<span className="text-[10px] text-ark-fg-dim">{(detail?.sources?.length ?? availableSources.length)} sources</span>}
                        >
                            <ul className="space-y-1.5 text-sm">
                                {(detail?.sources?.length
                                    ? detail.sources.map(s => ({
                                        key: s.key, label: s.label,
                                        freq: normalizeFrequency(s.frequency),
                                        unit: s.unit, points: s.points, liveness: s.liveness,
                                    }))
                                    : availableSources.map(s => {
                                        const c = covFor(selectedCommodity ?? '')[s]
                                        return {
                                            key: s, label: SOURCE_LABELS[s] ?? s,
                                            freq: freqOf(selectedCommodity ?? '', s),
                                            unit: c?.unit, points: c?.points ?? 0, liveness: c?.liveness,
                                        }
                                    })
                                ).map(s => (
                                    <li key={s.key} className="flex items-start justify-between gap-2">
                                        <button
                                            type="button"
                                            className="text-left text-ark-fg hover:text-emerald-300"
                                            onClick={() => selectedCommodity && selectCommodity(selectedCommodity, s.key)}
                                        >
                                            {s.label}
                                            <span className="block text-[11px] text-ark-fg-dim">
                                                {s.points.toLocaleString()} obs
                                                {s.unit ? ` · ${s.unit}` : ''}
                                                {s.liveness?.last_real_observation
                                                    ? ` · last real ${s.liveness.last_real_observation.slice(0, 7)}`
                                                    : ''}
                                            </span>
                                        </button>
                                        <FreqBadge freq={s.freq as Frequency} />
                                    </li>
                                ))}
                            </ul>
                        </RailBlock>

                        {/* Regional variants */}
                        {detail?.regional && detail.regional.length > 0 && (
                            <RailBlock title="Regional variants">
                                <ul className="space-y-1.5 text-sm">
                                    {detail.regional.map(r => (
                                        <li key={r.slug} className="flex items-center justify-between gap-2">
                                            <button
                                                type="button"
                                                className="text-left text-ark-fg hover:text-emerald-300"
                                                onClick={() => selectCommodity(r.slug)}
                                            >
                                                {r.region ?? r.label}
                                            </button>
                                            <span className="text-ark-fg-dim text-xs">
                                                {r.latest
                                                    ? `${fmtPrice(r.latest.price, r.unit ?? undefined)} · ${String(r.latest.date).slice(0, 7)}`
                                                    : 'no recent value'}
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                            </RailBlock>
                        )}

                        {/* Farm -> wholesale -> retail wedge */}
                        {detail?.wedge && (detail.wedge.ppi || detail.wedge.wholesale) && (
                            <RailBlock title="Wholesale ↔ retail">
                                <ul className="space-y-2 text-sm">
                                    {detail.wedge.wholesale && (
                                        <li>
                                            <span className="text-ark-fg-dim">Wholesale (USDA AMS terminal markets)</span>
                                            <div className="text-ark-fg">
                                                {detail.wedge.wholesale.low != null && detail.wedge.wholesale.high != null
                                                    ? `$${detail.wedge.wholesale.low.toFixed(2)}–$${detail.wedge.wholesale.high.toFixed(2)} per ${detail.wedge.wholesale.unit ?? 'package'}`
                                                    : '—'}
                                                <span className="text-xs text-ark-fg-dim">
                                                    {' '}· {detail.wedge.wholesale.cities ?? 0} cities
                                                    {detail.wedge.wholesale.varieties ? `, ${detail.wedge.wholesale.varieties} varieties` : ''}
                                                    {detail.wedge.wholesale.latest_date ? ` · ${String(detail.wedge.wholesale.latest_date).slice(0, 10)}` : ''}
                                                </span>
                                            </div>
                                            <Link to={`/wholesale?commodity=${encodeURIComponent(detail.wedge.wholesale.commodity ?? '')}`} className="text-xs text-emerald-400 hover:text-emerald-300">
                                                Every wholesale line for this item →
                                            </Link>
                                        </li>
                                    )}
                                    {detail.wedge.ppi && (
                                        <li>
                                            <span className="text-ark-fg-dim">
                                                Wholesale index (BLS PPI {detail.wedge.ppi.series_id})
                                            </span>
                                            <div className="text-ark-fg">
                                                {detail.wedge.ppi.latest
                                                    ? `${detail.wedge.ppi.latest.value.toLocaleString(undefined, { maximumFractionDigits: 1 })} · ${String(detail.wedge.ppi.latest.date).slice(0, 7)}`
                                                    : '—'}
                                            </div>
                                        </li>
                                    )}
                                    {detail.wedge.retail && (
                                        <li>
                                            <span className="text-ark-fg-dim">Retail (BLS Average Price)</span>
                                            <div className="text-ark-fg">
                                                {detail.wedge.retail.latest
                                                    ? `${fmtPrice(detail.wedge.retail.latest.price, detail.wedge.retail.unit)} · ${String(detail.wedge.retail.latest.date).slice(0, 7)}`
                                                    : '—'}
                                            </div>
                                        </li>
                                    )}
                                </ul>
                                <p className="text-[11px] text-ark-fg-dim mt-2">
                                    Wholesale is quoted per shipping package and retail per pound, so the
                                    two are not directly subtractable — the gap between them is shown as
                                    the publishers report it, not as a computed margin.
                                </p>
                            </RailBlock>
                        )}

                        {/* Provenance, inline — not on a separate page */}
                        <RailBlock title="Provenance">
                            <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
                                <dt className="text-ark-fg-dim">Publisher</dt>
                                <dd className="text-ark-fg">{detail?.provenance?.publisher ?? series?.label ?? '—'}</dd>
                                <dt className="text-ark-fg-dim">Series</dt>
                                <dd className="text-ark-fg font-mono text-xs break-all">
                                    {detail?.provenance?.series_id_or_item ?? itemLabel}
                                </dd>
                                <dt className="text-ark-fg-dim">Geography</dt>
                                <dd className="text-ark-fg">{detail?.provenance?.geography ?? '—'}</dd>
                                <dt className="text-ark-fg-dim">Unit as published</dt>
                                <dd className="text-ark-fg">{nativeUnit ?? detail?.provenance?.unit ?? 'not published'}</dd>
                                <dt className="text-ark-fg-dim">Last real observation</dt>
                                <dd className="text-ark-fg">
                                    {covFor(selectedCommodity ?? '')[selectedSource as SourceKey]?.liveness?.last_real_observation?.slice(0, 10) ?? '—'}
                                </dd>
                            </dl>
                            {detail?.provenance?.retrieval_url && (
                                <a
                                    href={detail.provenance.retrieval_url}
                                    target="_blank" rel="noopener noreferrer"
                                    className="text-xs text-emerald-400 hover:text-emerald-300 mt-2 inline-block break-all"
                                >
                                    Check this series at the publisher →
                                </a>
                            )}
                            <p className="text-[11px] text-ark-fg-dim mt-2">
                                Every series on this site is classified by its LAST REAL OBSERVATION, never
                                by a declared end date — fifteen BLS items carry a 2025 placeholder whose
                                real data is years older. Full per-source freshness on{' '}
                                <Link to="/sources" className="text-emerald-400 hover:text-emerald-300">Sources</Link>.
                            </p>
                        </RailBlock>
                    </div>

                    {/* ---- COMPARE TRAY ------------------------------------------- */}
                    {pinned.length > 0 && (
                        <div className="card">
                            <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                                <h3 className="text-sm font-semibold uppercase tracking-wide text-ark-fg-dim">
                                    Comparison tray ({pinned.length}/6)
                                </h3>
                                <div className="flex gap-2">
                                    <Link
                                        to={`/compare?series=${encodeURIComponent(pinned.join(','))}`}
                                        className="ark-btn ark-btn-sm"
                                    >
                                        Compare these →
                                    </Link>
                                    <button className="ark-btn ark-btn-sm ark-btn-ghost" onClick={() => setParam({ pin: null })}>
                                        Clear
                                    </button>
                                </div>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {pinned.map(p => {
                                    const [slug, src] = p.split(':')
                                    return (
                                        <span key={p} className="inline-flex items-center gap-1.5 text-xs bg-ark-tag border border-ark-line rounded px-2 py-1">
                                            <button onClick={() => selectCommodity(slug, src)} className="text-ark-fg hover:text-emerald-300">
                                                {displayNames[slug] ?? slug} · {SOURCE_LABELS[src] ?? src}
                                            </button>
                                            <button
                                                aria-label={`Remove ${slug}`}
                                                onClick={() => setParam({ pin: pinned.filter(x => x !== p).join(',') })}
                                                className="text-ark-fg-dim hover:text-rose-300"
                                            >
                                                <X className="w-3 h-3" />
                                            </button>
                                        </span>
                                    )
                                })}
                            </div>
                        </div>
                    )}

                    {/* ---- THE PLOTTED DATA -------------------------------------- */}
                    {chartData.length > 0 && (
                        <div className="card">
                            <ScrollableDataTable
                                rows={csvRows.map(r => ({ date: r.date.slice(0, 10), value: r.value }))}
                                columns={[
                                    { key: 'date', label: freq === 'annual' ? 'Year' : 'Month' },
                                    { key: 'value', label: axisUnit, numeric: true },
                                ]}
                                filename={fileStem}
                            />
                        </div>
                    )}

                    {/* Honest scope note, at the bottom where an explanation belongs. */}
                    <p className="text-xs text-ark-fg-dim">
                        Categories are kitchen categories; “Specialty &amp; Non-Food” holds real
                        agricultural series that are not kitchen inputs (cotton, wool, tobacco, hay).
                        Coverage badges are computed from the data itself.
                        {excludedSingleYear > 0 && (
                            <> {excludedSingleYear} single-year-only commodit
                                {excludedSingleYear === 1 ? 'y is' : 'ies are'} hidden — a series needs at
                                least two distinct years to be charted.</>
                        )}
                        {' '}Bulk data, code and methodology are on{' '}
                        <Link to="/data" className="text-emerald-400 hover:text-emerald-300">Data &amp; Code</Link>.
                    </p>
                </main>
            </div>
        </div>
    )
}
