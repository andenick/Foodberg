import { Route, Routes } from 'react-router-dom'
import Footer from './components/common/Footer'
import Header from './components/common/Header'
import CommodityDetail from './pages/CommodityDetail'
import DataSources from './pages/DataSources'
import FoodPriceIndex from './pages/FoodPriceIndex'
import GeographicPrices from './pages/GeographicPrices'
import HistoricalTrends from './pages/HistoricalTrends'
import HomePage from './pages/HomePage'
import PriceExplorer from './pages/PriceExplorer'

function App() {
    return (
        <div className="min-h-screen flex flex-col">
            <Header />
            <main className="flex-1">
                <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/index" element={<FoodPriceIndex />} />
                    <Route path="/explore" element={<PriceExplorer />} />
                    <Route path="/commodity/:commodityId" element={<CommodityDetail />} />
                    <Route path="/geographic" element={<GeographicPrices />} />
                    <Route path="/trends" element={<HistoricalTrends />} />
                    <Route path="/sources" element={<DataSources />} />
                </Routes>
            </main>
            <Footer />
        </div>
    )
}

export default App
