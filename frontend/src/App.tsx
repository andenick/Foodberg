import { Link, Navigate, Route, Routes, useLocation, useSearchParams } from 'react-router-dom'
import ArcanumChrome, { type Ecosystem, type NavItem } from './arcanum/ArcanumChrome'
import { type Cdf } from './arcanum/ArkTriad'
import ecosystemData from './arcanum/ecosystem.json'
import CommodityDetail from './pages/CommodityDetail'
import Compare from './pages/Compare'
import DataAndCode from './pages/DataAndCode'
import DataSources from './pages/DataSources'
import FoodPriceIndex from './pages/FoodPriceIndex'
import GeographicPrices from './pages/GeographicPrices'
import HistoricalTrends from './pages/HistoricalTrends'
import PriceExplorer from './pages/PriceExplorer'
import Seasons from './pages/Seasons'
import SupplyDemand from './pages/SupplyDemand'
import WholesalePrices from './pages/WholesalePrices'

// Canonical Arcanum Research ecosystem manifest (bundled statically — no CDN).
const ecosystem = ecosystemData as unknown as Ecosystem

// This site's Code-&-Data-First triad targets (drives the action footer).
const FOODBERG_CDF = (ecosystem.sites?.find((s) => s.key === 'foodberg') as unknown as { cdf?: Cdf } | undefined)?.cdf ?? null

// ---------------------------------------------------------------------------
// THE CHEF-FIRST INFORMATION ARCHITECTURE (2026-07-25)
//
// Before this, `/` was a hero + "⬇ Download the Data · ⬇ Download the Code" and
// the first nav item was `Food Index` — a composite index, not a price. `/` was
// not in the nav at all. A chef's first click landed on an index page.
//
// Now the Price Explorer IS `/`, and the nav is ordered for the audience the
// site declares. The Research Triad relocates to `/data` under the RATIFIED
// tool-first exception (CODE_DATA_FIRST_STANDARD §9.1, Foodberg registered
// 2026-07-25) — the compact triad still rides the action footer on every page,
// `/llms.txt`, the stable bundle URLs and the no-JSON rule are unchanged, and
// D13 is asserted against `/data` via `check_cdf.py --tool-first`. That is a
// retargeted gate, not a waived one.
// ---------------------------------------------------------------------------
const NAV: NavItem[] = [
    { label: 'Prices', href: '/' },
    { label: 'History', href: '/trends' },
    { label: 'Compare', href: '/compare' },
    { label: 'Seasons', href: '/seasons' },
    { label: 'Sources', href: '/sources' },
    { label: 'Data & Code', href: '/data' },
]

// The primary nav is deliberately six items — a chef's six questions. The
// research-grade surfaces are NOT orphaned by that: they get an always-visible
// secondary strip, so every route stays one click from every page. A page that
// exists but cannot be reached is exactly the defect this strip prevents.
const MORE_VIEWS: NavItem[] = [
    { label: 'Wholesale (daily, by city)', href: '/wholesale' },
    { label: 'Food Price Index', href: '/index' },
    { label: 'Supply & Demand', href: '/supply-demand' },
    { label: 'Geographic', href: '/geographic' },
]

function MoreViews({ activePath }: { activePath: string }) {
    return (
        <nav aria-label="More views" className="border-b border-ark-line bg-ark-bg-soft/60">
            <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-1.5 flex items-center gap-x-4 gap-y-1 flex-wrap">
                <span className="text-[11px] uppercase tracking-wide text-ark-fg-dim/70">More views</span>
                {MORE_VIEWS.map((item) => (
                    <Link
                        key={item.href}
                        to={item.href}
                        className={`text-xs transition-colors ${activePath === item.href
                            ? 'text-emerald-400 font-medium'
                            : 'text-ark-fg-dim hover:text-ark-fg'}`}
                    >
                        {item.label}
                    </Link>
                ))}
            </div>
        </nav>
    )
}

/** Preserve the query string across a route rename, so every /explore?commodity=…
 *  link ever published — including the hub's and nickanderson.us's — still lands
 *  on the same series instead of silently dropping its deep-link. */
function RedirectPreservingQuery({ to }: { to: string }) {
    const [params] = useSearchParams()
    const qs = params.toString()
    return <Navigate to={qs ? `${to}?${qs}` : to} replace />
}

function App() {
    const location = useLocation()
    return (
        <ArcanumChrome
            siteKey="foodberg"
            accent="#ea580c"
            accentSoft="#472313"
            nav={NAV}
            dprUrl="/sources"
            dprLabel="Data Sources"
            ecosystem={ecosystem}
            cdf={FOODBERG_CDF}
            activePath={location.pathname}
        >
            <MoreViews activePath={location.pathname} />
            <Routes>
                {/* The tool IS the front door. */}
                <Route path="/" element={<PriceExplorer />} />

                <Route path="/trends" element={<HistoricalTrends />} />
                <Route path="/compare" element={<Compare />} />
                <Route path="/seasons" element={<Seasons />} />
                <Route path="/sources" element={<DataSources />} />
                {/* The relocated Research Triad lives here (CDF §9.1 tool-first). */}
                <Route path="/data" element={<DataAndCode />} />

                {/* Research-grade surfaces, reachable from the More-views strip. */}
                <Route path="/wholesale" element={<WholesalePrices />} />
                <Route path="/index" element={<FoodPriceIndex />} />
                <Route path="/supply-demand" element={<SupplyDemand />} />
                <Route path="/geographic" element={<GeographicPrices />} />
                <Route path="/commodity/:commodityId" element={<CommodityDetail />} />

                {/* Legacy routes. /explore was the explorer's old home and is linked
                    from the hub, from nickanderson.us and from published deep-links;
                    /downloads folded into the new Data & Code tab. Both redirect
                    rather than 404. */}
                <Route path="/explore" element={<RedirectPreservingQuery to="/" />} />
                <Route path="/downloads" element={<RedirectPreservingQuery to="/data" />} />

                {/* Unmatched paths previously rendered a silent blank page. */}
                <Route path="*" element={
                    <div className="max-w-7xl mx-auto px-4 py-24 text-center">
                        <h1 className="text-3xl font-bold text-ark-fg mb-3">Page not found</h1>
                        <p className="text-ark-fg-dim mb-6">That address doesn't exist on Foodberg.</p>
                        <Link to="/" className="text-emerald-400 hover:text-emerald-300">← Back to prices</Link>
                    </div>
                } />
            </Routes>
        </ArcanumChrome>
    )
}

export default App
