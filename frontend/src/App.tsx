import { Link, Route, Routes, useLocation } from 'react-router-dom'
import ArcanumChrome, { type Ecosystem, type NavItem } from './arcanum/ArcanumChrome'
import { type Cdf } from './arcanum/ArkTriad'
import ecosystemData from './arcanum/ecosystem.json'
import CommodityDetail from './pages/CommodityDetail'
import DataSources from './pages/DataSources'
import Downloads from './pages/Downloads'
import FoodPriceIndex from './pages/FoodPriceIndex'
import GeographicPrices from './pages/GeographicPrices'
import HistoricalTrends from './pages/HistoricalTrends'
import HomePage from './pages/HomePage'
import PriceExplorer from './pages/PriceExplorer'
import SupplyDemand from './pages/SupplyDemand'

// Canonical Arcanum Research ecosystem manifest (bundled statically — no CDN).
const ecosystem = ecosystemData as unknown as Ecosystem

// This site's Code-&-Data-First triad targets (drives the action footer).
const FOODBERG_CDF = (ecosystem.sites?.find((s) => s.key === 'foodberg') as unknown as { cdf?: Cdf } | undefined)?.cdf ?? null

// Foodberg's real views, mapped to the shared-chrome nav.
const NAV: NavItem[] = [
    { label: 'Food Index', href: '/index' },
    { label: 'Price Explorer', href: '/explore' },
    { label: 'Supply & Demand', href: '/supply-demand' },
    { label: 'Geographic', href: '/geographic' },
    { label: 'Trends', href: '/trends' },
    { label: 'Downloads', href: '/downloads' },
    { label: 'Data Sources', href: '/sources' },
]

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
            <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/index" element={<FoodPriceIndex />} />
                <Route path="/explore" element={<PriceExplorer />} />
                <Route path="/supply-demand" element={<SupplyDemand />} />
                <Route path="/commodity/:commodityId" element={<CommodityDetail />} />
                <Route path="/geographic" element={<GeographicPrices />} />
                <Route path="/trends" element={<HistoricalTrends />} />
                <Route path="/downloads" element={<Downloads />} />
                <Route path="/sources" element={<DataSources />} />
                {/* Unmatched paths previously rendered a silent blank page. */}
                <Route path="*" element={
                    <div className="max-w-7xl mx-auto px-4 py-24 text-center">
                        <h1 className="text-3xl font-bold text-ark-fg mb-3">Page not found</h1>
                        <p className="text-ark-fg-dim mb-6">That address doesn't exist on Foodberg.</p>
                        <Link to="/" className="text-emerald-400 hover:text-emerald-300">← Back to the Food Index</Link>
                    </div>
                } />
            </Routes>
        </ArcanumChrome>
    )
}

export default App
