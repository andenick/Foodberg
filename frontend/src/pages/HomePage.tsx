import { ArrowRight, BarChart3, Database, Globe, History, TrendingUp } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'

// Shape of the /api/data/status response we rely on (only the fields used here).
interface DataStatusSource {
    name: string
    records?: number
    date_range?: { min: string | null; max: string | null }
}
interface DataStatus {
    sources: Record<string, DataStatusSource>
}

// Pull the 4-digit year out of a status date string ("2025" or "1990-01-01 …").
function yearOf(d: string | null | undefined): number | null {
    if (!d) return null
    const m = String(d).match(/\d{4}/)
    return m ? parseInt(m[0], 10) : null
}

// Format a record count compactly without inventing precision (e.g. 470108 -> "470K+").
function compactCount(n: number): string {
    if (n >= 1_000_000) return `${Math.floor(n / 1_000_000)}M+`
    if (n >= 1_000) return `${Math.floor(n / 1_000)}K+`
    return String(n)
}

export default function HomePage() {
    // Live headline stats sourced from /api/data/status. We compute what the
    // endpoint actually exposes (record total, source count, year span) and
    // fall back to honest, footnoted defaults only if the call fails. The
    // commodity count is NOT in /api/data/status, so it stays a footnoted
    // as-of figure rather than a silently-drifting literal.
    const COMMODITIES_AS_OF = '2025'
    const COMMODITIES_COUNT = '35' // distinct WASDE commodities in the database as of 2025
    const [liveStats, setLiveStats] = useState<{
        records: string
        sources: string
        years: string
        live: boolean
    }>({ records: '—', sources: '—', years: '—', live: false })

    useEffect(() => {
        let cancelled = false
        api.getDataStatus()
            .then((res) => {
                if (cancelled) return
                const status = res.data as DataStatus
                const sources = status?.sources ?? {}
                const entries = Object.values(sources).filter((s) => typeof s.records === 'number')
                const totalRecords = entries.reduce((sum, s) => sum + (s.records || 0), 0)
                const years: number[] = []
                for (const s of entries) {
                    const lo = yearOf(s.date_range?.min)
                    const hi = yearOf(s.date_range?.max)
                    if (lo) years.push(lo)
                    if (hi) years.push(hi)
                }
                const span = years.length ? Math.max(...years) - Math.min(...years) + 1 : null
                setLiveStats({
                    records: totalRecords > 0 ? compactCount(totalRecords) : '—',
                    sources: String(Object.keys(sources).length || '—'),
                    years: span ? `${span}` : '—',
                    live: totalRecords > 0,
                })
            })
            .catch(() => {
                // Network/endpoint failure: leave honest placeholders; never fabricate.
                if (!cancelled) setLiveStats((s) => ({ ...s, live: false }))
            })
        return () => { cancelled = true }
    }, [])
    const features = [
        {
            icon: TrendingUp,
            title: 'Price Explorer',
            description: 'Browse historical food commodity prices from USDA, FAO, and global markets',
            link: '/explore',
            color: 'text-emerald-400'
        },
        {
            icon: Globe,
            title: 'Geographic Comparison',
            description: 'Compare food prices across different regions and countries with side-by-side line comparisons',
            link: '/geographic',
            color: 'text-blue-400'
        },
        {
            icon: History,
            title: 'Historical Trends',
            description: 'Explore long-term price trends and compare multiple commodities over time',
            link: '/trends',
            color: 'text-purple-400'
        },
        {
            icon: Database,
            title: 'Data Sources',
            description: 'Learn about our data sources: USDA WASDE, FAO, FRED, BLS, and more',
            link: '/sources',
            color: 'text-amber-400'
        }
    ]

    // Headline stats. Three are computed live from /api/data/status (record
    // total, source count, year span); Commodities carries an explicit as-of
    // footnote because the status endpoint does not expose a commodity count.
    const stats: Array<{ label: string; value: string; footnote?: string }> = [
        { label: 'Commodities', value: `${COMMODITIES_COUNT}+`, footnote: `as of ${COMMODITIES_AS_OF}` },
        { label: 'Data Sources', value: liveStats.sources },
        { label: 'Years of Data', value: liveStats.years === '—' ? '—' : `${liveStats.years}+` },
        { label: 'Price Records', value: liveStats.records },
    ]

    // Featured commodities link into the Price Explorer pre-selected to that
    // commodity. ONLY genuine multi-year series are featured: each of these has
    // a continuous 1990s→present global-spot price series in the database
    // (verified against /api/data/status global_prices coverage). We deliberately
    // do NOT link to /commodity/<slug> (the WASDE detail page is single-year-2025
    // only) and we do NOT feature soybeans/rice/cattle, which have no multi-year
    // spot series — a featured tile must never land on a single-year view.
    const sampleCommodities = [
        { name: 'Wheat' },
        { name: 'Corn' },
        { name: 'Coffee' },
        { name: 'Sugar' },
        { name: 'Cotton' },
    ]

    return (
        <div className="min-h-screen">
            {/* Hero Section */}
            <section className="py-20 px-4 sm:px-6 lg:px-8">
                <div className="max-w-7xl mx-auto text-center">
                    <h1 className="text-5xl sm:text-6xl font-bold text-ark-fg mb-6">
                        Explore the History of
                        <span className="text-emerald-400"> Food Prices</span>
                    </h1>
                    <p className="text-xl text-ark-fg-dim mb-8 max-w-3xl mx-auto">
                        A comprehensive tool for historically-minded chefs and researchers to understand
                        the broader environmental and historical context of food commodity prices.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <Link to="/index" className="btn-primary text-lg px-8 py-3 inline-flex items-center justify-center space-x-2">
                            <BarChart3 className="w-5 h-5" />
                            <span>Food Price Index</span>
                        </Link>
                        <Link to="/explore" className="btn-secondary text-lg px-8 py-3 inline-flex items-center justify-center space-x-2">
                            <TrendingUp className="w-5 h-5" />
                            <span>Explore Prices</span>
                        </Link>
                    </div>
                </div>
            </section>

            {/* Stats */}
            <section className="py-12 px-4 sm:px-6 lg:px-8 bg-ark-bg-soft">
                <div className="max-w-7xl mx-auto">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                        {stats.map((stat) => (
                            <div key={stat.label} className="text-center">
                                <div className="text-4xl font-bold text-emerald-400 mb-2">{stat.value}</div>
                                <div className="text-sm text-ark-fg-dim">{stat.label}</div>
                                {stat.footnote && (
                                    <div className="text-xs text-ark-fg-dim/70 mt-1">{stat.footnote}</div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Quick Commodity Overview */}
            <section className="py-12 px-4 sm:px-6 lg:px-8">
                <div className="max-w-7xl mx-auto">
                    <h2 className="text-2xl font-bold text-ark-fg mb-6 text-center">Featured Commodities</h2>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                        {sampleCommodities.map((commodity) => (
                            <Link
                                key={commodity.name}
                                to={`/explore?commodity=${commodity.name.toLowerCase()}`}
                                className="card hover:border-emerald-500/50 transition-all text-center p-4"
                            >
                                <h3 className="text-lg font-medium text-ark-fg">{commodity.name}</h3>
                                <span className="text-sm text-ark-fg-dim">View history →</span>
                            </Link>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features Grid */}
            <section className="py-20 px-4 sm:px-6 lg:px-8">
                <div className="max-w-7xl mx-auto">
                    <h2 className="text-3xl font-bold text-ark-fg mb-12 text-center">
                        Understand Food Price History
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {features.map((feature) => {
                            const Icon = feature.icon
                            return (
                                <Link
                                    key={feature.title}
                                    to={feature.link}
                                    className="card hover:shadow-2xl hover:border-ark-line transition-all group"
                                >
                                    <Icon className={`w-12 h-12 ${feature.color} mb-4 group-hover:scale-110 transition-transform`} />
                                    <h3 className="text-xl font-semibold text-ark-fg mb-2">{feature.title}</h3>
                                    <p className="text-ark-fg-dim">{feature.description}</p>
                                    <div className="mt-4 flex items-center text-emerald-400 group-hover:translate-x-2 transition-transform">
                                        <span className="text-sm font-medium">Explore</span>
                                        <ArrowRight className="w-4 h-4 ml-2" />
                                    </div>
                                </Link>
                            )
                        })}
                    </div>
                </div>
            </section>

            {/* Historical Context Quote */}
            <section className="py-16 px-4 sm:px-6 lg:px-8 bg-ark-bg-soft">
                <div className="max-w-4xl mx-auto text-center">
                    <blockquote className="text-2xl italic text-ark-fg-dim mb-4">
                        "Tell me what you eat, and I will tell you what you are."
                    </blockquote>
                    <cite className="text-ark-fg-dim">— Jean Anthelme Brillat-Savarin, 1825</cite>
                    <p className="mt-6 text-ark-fg-dim">
                        Understanding food prices helps us understand history itself — from agricultural
                        revolutions to trade wars, climate events to economic crises.
                    </p>
                </div>
            </section>
        </div>
    )
}
