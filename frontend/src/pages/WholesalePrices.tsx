import { Truck } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../services/api'
import { downloadCsv } from '../arcanum/arkChartTheme'

/**
 * USDA AMS Market News — daily terminal-market wholesale prices.
 *
 * This is the only daily source on the site, and the only one that answers the
 * question a kitchen actually asks: not "what is the tomato index" but "what
 * does a 25 lb carton of vine-ripe tomatoes out of Mexico cost in the Bronx
 * today". The package, the origin, the variety and the grade ARE the value, so
 * nothing here is averaged or collapsed — every row is one published price
 * line, exactly as AMS printed it.
 */

interface Market {
    city: string
    state: string | null
    market: string
    rows: number
    commodities: number
    first_report_date: string
    last_report_date: string
}

interface CommodityEntry {
    commodity: string
    category: string | null
    rows: number
    cities: number
    varieties: number
    packages: number
    origins: number
    first_report_date: string
    last_report_date: string
}

interface PriceRow {
    report_date: string
    market: string
    city: string
    state: string | null
    commodity: string
    variety: string | null
    package: string | null
    grade: string | null
    item_size: string | null
    organic: string | null
    origin: string | null
    low_price: number | null
    high_price: number | null
    mostly_low_price: number | null
    mostly_high_price: number | null
    unit: string | null
    market_tone_comments: string | null
}

const PAGE_SIZE = 100

function priceLabel(r: PriceRow): string {
    const lo = r.low_price
    const hi = r.high_price
    if (lo == null && hi == null) return '—'
    if (lo != null && hi != null && lo !== hi) return `${lo.toFixed(2)} – ${hi.toFixed(2)}`
    return (lo ?? hi as number).toFixed(2)
}

export default function WholesalePrices() {
    const [markets, setMarkets] = useState<Market[]>([])
    const [commodities, setCommodities] = useState<CommodityEntry[]>([])
    const [rows, setRows] = useState<PriceRow[]>([])
    const [total, setTotal] = useState<number>(0)
    const [loading, setLoading] = useState(true)
    const [rowsLoading, setRowsLoading] = useState(false)
    const [meta, setMeta] = useState<{ licence?: string; frequency?: string; note?: string }>({})

    const [searchParams, setSearchParams] = useSearchParams()
    const commodity = searchParams.get('commodity') ?? 'Tomatoes'
    const city = searchParams.get('city') ?? ''
    const organic = searchParams.get('organic') ?? ''
    const filter = searchParams.get('q') ?? ''

    const setParam = (key: string, value: string) => {
        const next = new URLSearchParams(searchParams)
        if (value) next.set(key, value); else next.delete(key)
        setSearchParams(next, { replace: true })
    }

    useEffect(() => {
        Promise.all([api.getWholesaleMarkets(), api.getWholesaleCommodities()])
            .then(([mRes, cRes]) => {
                setMarkets(mRes.data.markets || [])
                setCommodities(cRes.data.commodities || [])
                setMeta({
                    licence: mRes.data.licence,
                    frequency: mRes.data.frequency,
                })
            })
            .catch((e) => console.error('Failed to load wholesale catalogs:', e))
            .finally(() => setLoading(false))
    }, [])

    useEffect(() => {
        setRowsLoading(true)
        api.searchWholesale({
            commodity: commodity || undefined,
            city: city || undefined,
            organic: organic || undefined,
            limit: PAGE_SIZE,
        })
            .then((res) => {
                setRows(res.data.results || [])
                setTotal(res.data.total_matching ?? 0)
                setMeta((m) => ({ ...m, note: res.data.note }))
            })
            .catch((e) => { console.error('Wholesale search failed:', e); setRows([]); setTotal(0) })
            .finally(() => setRowsLoading(false))
    }, [commodity, city, organic])

    const visibleCommodities = useMemo(() => {
        const needle = filter.trim().toLowerCase()
        if (!needle) return commodities
        return commodities.filter(c => c.commodity.toLowerCase().includes(needle))
    }, [commodities, filter])

    const selected = commodities.find(c => c.commodity === commodity)
    const latestDate = rows.length ? rows[0].report_date : null

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-ark-fg mb-2 flex items-center">
                    <Truck className="w-8 h-8 mr-3 text-orange-400" />
                    Wholesale Prices — daily terminal markets
                </h1>
                <p className="text-ark-fg-dim">
                    USDA Agricultural Marketing Service Market News, published every business day
                    from the US terminal markets. Prices are quoted <strong>per package as
                    published</strong> — a 25 lb carton, a 5 kg flat, a 20 lb crate — and are never
                    averaged or collapsed across varieties, packages or origins, because for a
                    kitchen the package and the origin <em>are</em> the price.
                    {meta.licence ? <> {meta.licence}.</> : null}
                </p>
            </div>

            {loading ? (
                <div className="card text-ark-fg-dim">Loading the terminal-market catalog…</div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    {/* Commodity picker */}
                    <div className="lg:col-span-1">
                        <div className="card">
                            <h2 className="text-lg font-semibold text-ark-fg mb-3">
                                Commodity
                                <span className="text-sm text-ark-fg-dim ml-2">
                                    ({visibleCommodities.length}
                                    {visibleCommodities.length !== commodities.length
                                        ? ` of ${commodities.length}` : ''})
                                </span>
                            </h2>
                            <input
                                type="text"
                                value={filter}
                                onChange={(e) => setParam('q', e.target.value)}
                                placeholder="Filter — “tomato”, “basil”, “pepper”…"
                                className="w-full mb-3 px-3 py-2 bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg placeholder-ark-fg-dim focus:outline-none focus:border-orange-500"
                            />
                            <div className="space-y-1 max-h-[520px] overflow-y-auto">
                                {visibleCommodities.map(c => (
                                    <button
                                        key={c.commodity}
                                        onClick={() => setParam('commodity', c.commodity)}
                                        className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${c.commodity === commodity
                                            ? 'bg-orange-600/20 border border-orange-500/50'
                                            : 'bg-ark-bg-soft hover:bg-ark-tag border border-transparent'
                                            }`}
                                    >
                                        <span className="block text-sm font-medium text-ark-fg">
                                            {c.commodity}
                                        </span>
                                        <span className="block text-[11px] text-ark-fg-dim mt-0.5">
                                            {c.cities} cities · {c.packages} packages · {c.origins} origins
                                        </span>
                                    </button>
                                ))}
                                {visibleCommodities.length === 0 && (
                                    <p className="text-sm text-ark-fg-dim py-3">
                                        No commodity matches “{filter.trim()}”. AMS publishes
                                        {' '}{commodities.length} at these markets.
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Price lines */}
                    <div className="lg:col-span-3">
                        <div className="card">
                            <div className="flex justify-between items-start flex-wrap gap-3 mb-4">
                                <div>
                                    <h2 className="text-xl font-semibold text-ark-fg">{commodity}</h2>
                                    <p className="text-sm text-ark-fg-dim mt-1">
                                        {total.toLocaleString()} published price lines
                                        {selected ? <> · {selected.first_report_date} → {selected.last_report_date}</> : null}
                                        {latestDate ? <> · showing the most recent {Math.min(rows.length, PAGE_SIZE)}, latest {latestDate}</> : null}
                                    </p>
                                </div>
                                <button
                                    type="button"
                                    className="ark-btn ark-btn-sm ark-btn-ghost"
                                    disabled={rows.length === 0}
                                    onClick={() => downloadCsv(
                                        rows.map(r => ({
                                            report_date: r.report_date,
                                            city: r.city,
                                            market: r.market,
                                            commodity: r.commodity,
                                            variety: r.variety ?? '',
                                            package: r.package ?? '',
                                            grade: r.grade ?? '',
                                            item_size: r.item_size ?? '',
                                            organic: r.organic ?? '',
                                            origin: r.origin ?? '',
                                            low_price: r.low_price ?? '',
                                            high_price: r.high_price ?? '',
                                            unit: r.unit ?? '',
                                        })),
                                        `foodberg_wholesale_${commodity.replace(/[^a-z0-9]+/gi, '_').toLowerCase()}`,
                                    )}
                                >
                                    Download CSV
                                </button>
                            </div>

                            {/* Filters */}
                            <div className="flex gap-3 flex-wrap mb-4">
                                <select
                                    value={city}
                                    onChange={(e) => setParam('city', e.target.value)}
                                    className="px-3 py-2 bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg focus:outline-none focus:border-orange-500"
                                >
                                    <option value="">All cities</option>
                                    {markets.map(m => (
                                        <option key={m.city} value={m.city}>
                                            {m.city}{m.state ? `, ${m.state}` : ''}
                                        </option>
                                    ))}
                                </select>
                                <select
                                    value={organic}
                                    onChange={(e) => setParam('organic', e.target.value)}
                                    className="px-3 py-2 bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg focus:outline-none focus:border-orange-500"
                                >
                                    <option value="">Conventional and organic</option>
                                    <option value="Y">Organic only</option>
                                    <option value="N">Conventional only</option>
                                </select>
                            </div>

                            {rowsLoading ? (
                                <p className="text-ark-fg-dim py-8 text-center">Loading price lines…</p>
                            ) : rows.length === 0 ? (
                                <p className="text-ark-fg-dim py-8 text-center">
                                    No published price lines match these filters. This is a real
                                    result — AMS simply did not quote {commodity.toLowerCase()}
                                    {city ? ` in ${city}` : ''} under these conditions.
                                </p>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="text-left text-xs uppercase tracking-wide text-ark-fg-dim border-b border-ark-line">
                                                <th className="py-2 pr-3">Date</th>
                                                <th className="py-2 pr-3">City</th>
                                                <th className="py-2 pr-3">Variety</th>
                                                <th className="py-2 pr-3">Package</th>
                                                <th className="py-2 pr-3">Size / grade</th>
                                                <th className="py-2 pr-3">Origin</th>
                                                <th className="py-2 pr-3">Org.</th>
                                                <th className="py-2 pr-3 text-right">Price (USD)</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {rows.map((r, i) => (
                                                <tr
                                                    key={i}
                                                    className="border-b border-ark-line/50 hover:bg-ark-tag/40"
                                                >
                                                    <td className="py-2 pr-3 whitespace-nowrap text-ark-fg-dim">{r.report_date}</td>
                                                    <td className="py-2 pr-3 whitespace-nowrap text-ark-fg">{r.city}</td>
                                                    <td className="py-2 pr-3 text-ark-fg">{r.variety ?? '—'}</td>
                                                    <td className="py-2 pr-3 text-ark-fg">{r.package ?? '—'}</td>
                                                    <td className="py-2 pr-3 text-ark-fg-dim">
                                                        {[r.item_size, r.grade].filter(Boolean).join(' · ') || '—'}
                                                    </td>
                                                    <td className="py-2 pr-3 text-ark-fg-dim">{r.origin ?? '—'}</td>
                                                    <td className="py-2 pr-3 text-ark-fg-dim">
                                                        {r.organic === 'Y' ? 'organic' : ''}
                                                    </td>
                                                    <td className="py-2 pr-3 text-right font-medium text-ark-fg whitespace-nowrap">
                                                        {priceLabel(r)}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}

                            <p className="text-xs text-ark-fg-dim mt-4 pt-3 border-t border-ark-line">
                                Source: USDA AMS Market News (MARS API v3.1)
                                {meta.frequency ? ` · ${meta.frequency}` : ''} ·
                                {' '}{meta.note ?? 'Rows are published price lines, not averages.'}
                                {' '}Full table: <a className="text-orange-400 hover:text-orange-300"
                                    href="/api/download/ams_wholesale_prices.csv">CSV</a>,{' '}
                                <a className="text-orange-400 hover:text-orange-300"
                                    href="/api/download/ams_wholesale_prices.xlsx">XLSX</a>,{' '}
                                <a className="text-orange-400 hover:text-orange-300"
                                    href="/api/download/ams_wholesale_prices.parquet">Parquet</a>.
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
