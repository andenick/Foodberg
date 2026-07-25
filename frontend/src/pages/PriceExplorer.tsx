import { BarChart3, Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
    CartesianGrid,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis
} from 'recharts'
import { api } from '../services/api'
import { downloadCsv, useArkTheme } from '../arcanum/arkChartTheme'
import { ChartMetaStrip, ScrollableDataTable } from '../components/ChartDetails'

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
    start: string
    end: string
    label?: string
    n_years?: number
    unit?: string
    liveness?: Liveness
}

const LIVENESS_STYLE: Record<string, string> = {
    stale: 'text-amber-300 bg-amber-900/30',
    discontinued: 'text-rose-300 bg-rose-900/30',
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

type Coverage = Partial<Record<'av' | 'nass' | 'pinksheet' | 'retail', SourceCov>>

interface SeriesRow { date: string; year: number; price: number }

interface SourcePayload {
    commodity: string
    source: string
    has_history: boolean
    label?: string
    unit?: string | null
    data_points: number
    date_range?: { start: string; end: string }
    data: SeriesRow[]
    note?: string
}

const SOURCE_LABELS: Record<string, string> = {
    nass: 'US farm gate (USDA)',
    av: 'Global spot (monthly)',
    pinksheet: 'Global spot (Pink Sheet)',
    retail: 'US retail (BLS)',
}

// Preferred display order for source tabs.
const SOURCE_ORDER: Array<'nass' | 'av' | 'pinksheet' | 'retail'> = ['nass', 'av', 'pinksheet', 'retail']

// Commodities with a genuine multi-year Alpha-Vantage spot-price series
// (1992→present monthly), per the backend /api/prices/history contract. Used
// to resolve a /explore?commodity=… deep-link even when the commodity is not
// in the WASDE-derived selectable list.
const AV_HISTORY_COMMODITIES = new Set(['wheat', 'corn', 'coffee', 'sugar', 'cotton'])

export default function PriceExplorer() {
    const [coverage, setCoverage] = useState<Record<string, Coverage>>({})
    const [displayNames, setDisplayNames] = useState<Record<string, string>>({})
    const [selectedCategory, setSelectedCategory] = useState<string>('all')
    const [searchTerm, setSearchTerm] = useState('')
    const [loading, setLoading] = useState(true)
    const [series, setSeries] = useState<SourcePayload | null>(null)
    const [selectedCommodity, setSelectedCommodity] = useState<string | null>(null)
    const [selectedSource, setSelectedSource] = useState<string>('nass')
    const [fallbackValue, setFallbackValue] = useState<{ price: number; year: number; unit: string } | null>(null)
    const [searchHits, setSearchHits] = useState<SearchHit[] | null>(null)
    const [searching, setSearching] = useState(false)
    const [searchParams] = useSearchParams()
    const t = useArkTheme()

    useEffect(() => {
        api.getPriceCoverage()
            .then((covRes) => {
                setCoverage(covRes.data.commodities || {})
                setDisplayNames(covRes.data.display_names || {})
            })
            .catch((error) => console.error('Failed to load commodities:', error))
            .finally(() => setLoading(false))
    }, [])

    const covFor = (name: string): Coverage => coverage[name.toLowerCase()] ?? {}
    // A source is plottable only if it spans ≥2 distinct years (a real time
    // series). Prefer the explicit n_years count; fall back to points > 1 when
    // n_years isn't reported. This excludes WASDE-2025-only single-year series.
    const isMultiYear = (c?: SourceCov): boolean =>
        !!c && (c.n_years !== undefined ? c.n_years >= 2 : c.points > 1)
    const sourcesFor = (name: string) =>
        SOURCE_ORDER.filter((s) => isMultiYear(covFor(name)[s]))

    const loadSeries = async (commodity: string, source: string) => {
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
    }

    const selectCommodity = (commodity: string) => {
        const avail = sourcesFor(commodity)
        loadSeries(commodity, avail.length ? avail[0] : 'none')
    }

    // Deep-link support: /explore?commodity=wheat lands directly on that
    // commodity's series. Acts once the commodity/coverage data has loaded.
    // Resolution order: (1) if the commodity is in the loaded list and has a
    // multi-year source, select it normally; (2) otherwise, for the known
    // Alpha-Vantage spot-price commodities (genuine 1992→present monthly
    // history) load that series directly. The 'av' branch reads has_history
    // from the API, so nothing single-year or synthetic is ever charted.
    useEffect(() => {
        if (loading || selectedCommodity) return
        const want = (searchParams.get('commodity') || '').trim().toLowerCase()
        if (!want) return
        if (coverage[want] && sourcesFor(want).length > 0) {
            selectCommodity(want)
        } else if (AV_HISTORY_COMMODITIES.has(want)) {
            loadSeries(want, 'av')
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [loading, coverage, searchParams])

    // The browsable universe is every slug the coverage endpoint reports —
    // which since the Tier 0 backend fix includes all 47 BLS Average Price
    // items in their own right, not just the 11 that happened to be
    // hand-linked to a USDA NASS parent commodity.
    //
    // Commodities with NO multi-year source (single-year-only, e.g. WASDE 2025)
    // are excluded entirely — a series needs ≥2 distinct years to be selectable.
    const allSlugs = useMemo(() => Object.keys(coverage), [coverage])
    const items = useMemo<ExplorerItem[]>(() => allSlugs
        .filter(slug => sourcesFor(slug).length > 0)
        .map(slug => {
            const label = displayNames[slug] ?? slug
            return { slug, label, category: classifyCommodity(slug, displayNames[slug]) }
        }), [allSlugs, coverage, displayNames])
    const excludedSingleYear = allSlugs.length - items.length

    // Coverage-aware sort: most-covered commodities first.
    const filteredCommodities = useMemo(() => items
        .filter(c => {
            const needle = searchTerm.trim().toLowerCase()
            const matchesSearch = !needle
                || c.slug.includes(needle)
                || c.label.toLowerCase().includes(needle)
            if (selectedCategory === 'all') return matchesSearch
            return matchesSearch && c.category === selectedCategory
        })
        .sort((a, b) => {
            const an = sourcesFor(a.slug).length
            const bn = sourcesFor(b.slug).length
            return an !== bn ? bn - an : a.label.localeCompare(b.label)
        }), [items, searchTerm, selectedCategory, coverage])

    // Real, server-side search across the underlying price tables.
    //
    // Before this, the search box was a substring filter over the already
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
                    // Attach a browsable slug where the hit corresponds to a
                    // commodity this page can actually chart.
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

    const unitLabel = series?.unit || 'Value'
    const chartData = series?.data ?? []
    const latestRow = chartData.length ? chartData[chartData.length - 1] : null
    const availableSources = selectedCommodity ? sourcesFor(selectedCommodity) : []

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-ark-fg mb-2">Price Explorer</h1>
                <p className="text-ark-fg-dim">
                    Real price history from four baked sources — USDA farm-gate prices (annual,
                    many series back to 1908), global spot prices (Alpha Vantage and the World Bank
                    Pink Sheet, monthly), and US retail averages (BLS Average Price, monthly, in
                    $/lb, $/dozen and $/gallon). Categories are kitchen categories;
                    “Specialty &amp; Non-Food” holds real agricultural series that are not kitchen
                    inputs (cotton, wool, tobacco, hay). Coverage badges are computed from the data
                    itself; nothing is interpolated or extrapolated.
                    {excludedSingleYear > 0 && (
                        <> {excludedSingleYear} single-year-only commodit
                        {excludedSingleYear === 1 ? 'y is' : 'ies are'} hidden — a series needs at
                        least two distinct years to be charted.</>
                    )}
                </p>
            </div>

            {/* Search and Filters */}
            <div className="card mb-6">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-ark-fg-dim" />
                            <input
                                type="text"
                                placeholder="Search every price series — try “tomato”, “lettuce”, “bacon”…"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 bg-ark-tag border border-ark-line rounded-lg text-ark-fg placeholder-ark-fg-dim focus:outline-none focus:border-emerald-500"
                            />
                        </div>
                        {searchTerm.trim().length >= 2 && (
                            <div className="mt-1 text-xs text-ark-fg-dim">
                                {searching
                                    ? 'Searching the price tables…'
                                    : searchHits === null
                                        ? null
                                        : searchHits.length === 0
                                            ? `No series in the database matches “${searchTerm.trim()}”. This is a real result, not a truncated list — the search runs against every price table.`
                                            : `${filteredCommodities.length} browsable · ${searchHits.length} matching series in the underlying data`}
                            </div>
                        )}
                    </div>
                    <div className="flex gap-2 flex-wrap">
                        <button
                            onClick={() => setSelectedCategory('all')}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${selectedCategory === 'all'
                                    ? 'bg-emerald-600 text-white'
                                    : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                }`}
                        >
                            All
                        </button>
                        {KITCHEN_CATEGORIES.map(category => (
                            <button
                                key={category}
                                onClick={() => setSelectedCategory(category)}
                                className={`px-4 py-2 rounded-lg font-medium transition-colors ${selectedCategory === category
                                        ? 'bg-emerald-600 text-white'
                                        : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                    }`}
                            >
                                {category}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Commodity List */}
                <div className="lg:col-span-1">
                    <div className="card">
                        <h2 className="text-lg font-semibold text-ark-fg mb-4 flex items-center">
                            <BarChart3 className="w-5 h-5 mr-2 text-emerald-400" />
                            Commodities ({filteredCommodities.length})
                        </h2>

                        {loading ? (
                            <div className="text-center py-8">
                                <div className="animate-spin w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full mx-auto"></div>
                                <p className="text-ark-fg-dim mt-2">Loading commodities...</p>
                            </div>
                        ) : (
                            <div className="space-y-2 max-h-[600px] overflow-y-auto">
                                {filteredCommodities.length === 0 && (
                                    <p className="text-sm text-ark-fg-dim py-4">
                                        Nothing in this category matches
                                        {searchTerm.trim() ? ` “${searchTerm.trim()}”` : ''}.
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
                                    const live = best.sort(
                                        (a, b) => worstFirst.indexOf(a.status) - worstFirst.indexOf(b.status))[0]
                                    return (
                                        <button
                                            key={item.slug}
                                            onClick={() => selectCommodity(item.slug)}
                                            className={`w-full text-left p-3 rounded-lg transition-colors ${selectedCommodity === item.slug
                                                    ? 'bg-emerald-600/20 border border-emerald-500/50'
                                                    : 'bg-ark-bg-soft hover:bg-ark-tag border border-transparent'
                                                }`}
                                        >
                                            <div className="flex justify-between items-center gap-2">
                                                <span className={`font-medium text-ark-fg${isDisplayName ? '' : ' capitalize'}`}>
                                                    {item.label}
                                                </span>
                                                <span className="shrink-0 text-[10px] font-semibold uppercase tracking-wide text-emerald-400 bg-emerald-900/30 px-1.5 py-0.5 rounded">
                                                    {nSrc} source{nSrc > 1 ? 's' : ''}
                                                </span>
                                            </div>
                                            <div className="text-xs text-ark-fg-dim mt-1">
                                                {span ? `History ${span}` : 'Multi-year series'} · {item.category}
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

                        {/* Real server-side search results (/api/prices/search).
                            Shown so a term that matches data the browsable list
                            does not carry is still visible, with an honest
                            observation count, instead of a silent zero. */}
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
                                                    : 'text-ark-fg-dim cursor-default'
                                                }`}
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
                </div>

                {/* Price Chart */}
                <div className="lg:col-span-2">
                    <div className="card h-full">
                        {selectedCommodity && series ? (
                            <>
                                <div className="flex justify-between items-center mb-2 flex-wrap gap-2">
                                    <h2 className={`text-xl font-semibold text-ark-fg${displayNames[selectedCommodity] ? '' : ' capitalize'}`}>
                                        {displayNames[selectedCommodity] ?? selectedCommodity} — price history
                                    </h2>
                                    <div className="flex items-center gap-3 flex-wrap">
                                        <button
                                            type="button"
                                            className="ark-btn ark-btn-sm ark-btn-ghost"
                                            onClick={() => downloadCsv(
                                                chartData.map(r => ({ date: r.date, year: r.year, [unitLabel]: r.price })),
                                                `foodberg_${selectedCommodity}_${selectedSource}_prices`,
                                            )}
                                            disabled={chartData.length === 0}
                                        >
                                            Download CSV
                                        </button>
                                        {/* The commodity-detail route is built on the USDA
                                            WASDE universe; BLS-AP-only items have no page
                                            there, so the link is not offered for them. */}
                                        {!displayNames[selectedCommodity] && (
                                            <Link
                                                to={`/commodity/${selectedCommodity}`}
                                                className="text-sm text-emerald-400 hover:text-emerald-300"
                                            >
                                                View Details →
                                            </Link>
                                        )}
                                    </div>
                                </div>

                                {/* Source tabs */}
                                {availableSources.length > 0 && (
                                    <div className="flex gap-2 mb-4 flex-wrap">
                                        {availableSources.map((s) => (
                                            <button
                                                key={s}
                                                onClick={() => loadSeries(selectedCommodity, s)}
                                                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${selectedSource === s
                                                        ? 'bg-emerald-600 text-white'
                                                        : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                                                    }`}
                                            >
                                                {SOURCE_LABELS[s]}
                                            </button>
                                        ))}
                                    </div>
                                )}

                                {/* Never present a series the publisher stopped
                                    updating as if it were current (S5). */}
                                {(() => {
                                    const note = livenessNote(
                                        selectedCommodity
                                            ? covFor(selectedCommodity)[selectedSource as keyof Coverage]?.liveness
                                            : undefined)
                                    if (!note) return null
                                    return (
                                        <div className="mb-4 px-3 py-2 rounded-lg border border-amber-500/40 bg-amber-900/20 text-sm text-amber-200">
                                            {note}. The history below is real; the series is not current.
                                        </div>
                                    )
                                })()}

                                {series.has_history && chartData.length > 1 ? (
                                    <div className="h-[380px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={chartData} margin={{ left: 12, bottom: 8 }}>
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
                                                    label={{ value: unitLabel, angle: -90, position: 'insideLeft', fill: t.dim, fontSize: 12 }}
                                                />
                                                <Tooltip
                                                    contentStyle={t.tooltip}
                                                    labelStyle={{ color: t.fg }}
                                                    formatter={(value: number) => [value.toLocaleString(undefined, { maximumFractionDigits: 3 }), unitLabel]}
                                                />
                                                <Line
                                                    type="monotone"
                                                    dataKey="price"
                                                    stroke={t.accent}
                                                    strokeWidth={2}
                                                    dot={false}
                                                    activeDot={{ r: 6, fill: t.accent }}
                                                />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                ) : (
                                    /* Honest single-point view: a stat card, not a fake line. */
                                    <div className="h-[380px] flex flex-col items-center justify-center text-center">
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
                                        unit: unitLabel,
                                        dateRange: series.date_range
                                            ? `${series.date_range.start} → ${series.date_range.end}`
                                            : null,
                                        points: series.data_points,
                                        latestLabel: 'Latest',
                                        latestValue: latestRow
                                            ? `${latestRow.price.toLocaleString(undefined, { maximumFractionDigits: 3 })} (${latestRow.date})`
                                            : null,
                                    }}
                                />

                                <ScrollableDataTable
                                    rows={chartData.map(r => ({ date: r.date, value: r.price }))}
                                    columns={[
                                        { key: 'date', label: series.source === 'nass' ? 'Year' : 'Month' },
                                        { key: 'value', label: unitLabel, numeric: true },
                                    ]}
                                    filename={`foodberg_${selectedCommodity}_${selectedSource}_prices`}
                                />
                            </>
                        ) : selectedCommodity ? (
                            <div className="h-[400px] flex items-center justify-center text-ark-fg-dim">
                                Loading price data...
                            </div>
                        ) : (
                            <div className="h-[400px] flex flex-col items-center justify-center text-ark-fg-dim">
                                <BarChart3 className="w-16 h-16 mb-4 text-ark-fg-dim" />
                                <p className="text-lg">Select a commodity to view price history</p>
                                <p className="text-sm mt-2">Badges show how many real price sources each commodity has</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
