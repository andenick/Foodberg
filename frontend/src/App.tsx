import { Route, Routes, useLocation } from 'react-router-dom'
import ArcanumChrome, { type Ecosystem, type NavItem } from './arcanum/ArcanumChrome'
import ecosystemData from './arcanum/ecosystem.json'
import CommodityDetail from './pages/CommodityDetail'
import DataSources from './pages/DataSources'
import Downloads from './pages/Downloads'
import FoodPriceIndex from './pages/FoodPriceIndex'
import GeographicPrices from './pages/GeographicPrices'
import HistoricalTrends from './pages/HistoricalTrends'
import HomePage from './pages/HomePage'
import PriceExplorer from './pages/PriceExplorer'

// Canonical Arcanum Research ecosystem manifest (bundled statically — no CDN).
const ecosystem = ecosystemData as unknown as Ecosystem

// Foodberg's real views, mapped to the shared-chrome nav.
const NAV: NavItem[] = [
    { label: 'Food Index', href: '/index' },
    { label: 'Price Explorer', href: '/explore' },
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
            activePath={location.pathname}
        >
            <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/index" element={<FoodPriceIndex />} />
                <Route path="/explore" element={<PriceExplorer />} />
                <Route path="/commodity/:commodityId" element={<CommodityDetail />} />
                <Route path="/geographic" element={<GeographicPrices />} />
                <Route path="/trends" element={<HistoricalTrends />} />
                <Route path="/downloads" element={<Downloads />} />
                <Route path="/sources" element={<DataSources />} />
            </Routes>
        </ArcanumChrome>
    )
}

export default App
