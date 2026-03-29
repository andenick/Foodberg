import { BarChart3, Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
    CartesianGrid,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis
} from 'recharts'
import { api } from '../services/api'

// Commodity categories for filtering
const COMMODITY_CATEGORIES = {
    'Grains': ['wheat', 'corn', 'rice', 'barley', 'oats', 'sorghum', 'rye'],
    'Oilseeds': ['soybeans', 'canola', 'sunflower', 'peanuts', 'flaxseed'],
    'Livestock': ['cattle', 'hogs', 'sheep', 'goats', 'chickens', 'turkeys'],
    'Dairy & Eggs': ['milk', 'eggs'],
    'Fiber': ['cotton'],
    'Fruits': ['apples', 'grapes', 'blueberries', 'strawberries', 'cranberries'],
    'Other': ['hay', 'tobacco', 'honey', 'potatoes']
}

interface CommodityData {
    commodity: string
    filename: string
    last_updated: string
    file_size_mb: number
}

export default function PriceExplorer() {
    const [commodities, setCommodities] = useState<CommodityData[]>([])
    const [selectedCategory, setSelectedCategory] = useState<string>('all')
    const [searchTerm, setSearchTerm] = useState('')
    const [loading, setLoading] = useState(true)
    const [priceData, setPriceData] = useState<any[]>([])
    const [selectedCommodity, setSelectedCommodity] = useState<string | null>(null)

    useEffect(() => {
        loadCommodities()
    }, [])

    const loadCommodities = async () => {
        try {
            const response = await api.getWASDECommodities()
            setCommodities(response.data.commodities || [])
        } catch (error) {
            console.error('Failed to load commodities:', error)
        } finally {
            setLoading(false)
        }
    }

    const loadCommodityPrices = async (commodity: string) => {
        setSelectedCommodity(commodity)
        try {
            const response = await api.getWASDEData(commodity, 100)
            const data = response.data

            // Transform data for chart - group by year and get average values
            const yearlyData = data.data?.reduce((acc: any, record: any) => {
                const year = record.year
                if (!acc[year]) {
                    acc[year] = { year, values: [], count: 0 }
                }
                if (record.numeric_value) {
                    acc[year].values.push(record.numeric_value)
                    acc[year].count++
                }
                return acc
            }, {}) || {}

            const chartData = Object.values(yearlyData)
                .map((item: any) => ({
                    year: item.year,
                    price: item.values.length > 0
                        ? item.values.reduce((a: number, b: number) => a + b, 0) / item.values.length
                        : null
                }))
                .filter((item: any) => item.price !== null)
                .sort((a: any, b: any) => a.year - b.year)

            setPriceData(chartData)
        } catch (error) {
            console.error('Failed to load prices:', error)
        }
    }

    const filteredCommodities = commodities.filter(c => {
        const matchesSearch = c.commodity.toLowerCase().includes(searchTerm.toLowerCase())
        if (selectedCategory === 'all') return matchesSearch

        const categoryItems = COMMODITY_CATEGORIES[selectedCategory as keyof typeof COMMODITY_CATEGORIES] || []
        return matchesSearch && categoryItems.includes(c.commodity.toLowerCase())
    })

    const formatFileSize = (mb: number) => {
        if (mb < 1) return `${(mb * 1024).toFixed(0)} KB`
        return `${mb.toFixed(1)} MB`
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-slate-100 mb-2">Price Explorer</h1>
                <p className="text-slate-400">
                    Browse historical food commodity prices from USDA WASDE reports and other data sources
                </p>
            </div>

            {/* Search and Filters */}
            <div className="card mb-6">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                            <input
                                type="text"
                                placeholder="Search commodities..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:border-emerald-500"
                            />
                        </div>
                    </div>
                    <div className="flex gap-2 flex-wrap">
                        <button
                            onClick={() => setSelectedCategory('all')}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${selectedCategory === 'all'
                                    ? 'bg-emerald-600 text-white'
                                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                }`}
                        >
                            All
                        </button>
                        {Object.keys(COMMODITY_CATEGORIES).map(category => (
                            <button
                                key={category}
                                onClick={() => setSelectedCategory(category)}
                                className={`px-4 py-2 rounded-lg font-medium transition-colors ${selectedCategory === category
                                        ? 'bg-emerald-600 text-white'
                                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
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
                        <h2 className="text-lg font-semibold text-slate-100 mb-4 flex items-center">
                            <BarChart3 className="w-5 h-5 mr-2 text-emerald-400" />
                            Commodities ({filteredCommodities.length})
                        </h2>

                        {loading ? (
                            <div className="text-center py-8">
                                <div className="animate-spin w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full mx-auto"></div>
                                <p className="text-slate-400 mt-2">Loading commodities...</p>
                            </div>
                        ) : (
                            <div className="space-y-2 max-h-[600px] overflow-y-auto">
                                {filteredCommodities.map(commodity => (
                                    <button
                                        key={commodity.commodity}
                                        onClick={() => loadCommodityPrices(commodity.commodity)}
                                        className={`w-full text-left p-3 rounded-lg transition-colors ${selectedCommodity === commodity.commodity
                                                ? 'bg-emerald-600/20 border border-emerald-500/50'
                                                : 'bg-slate-700/50 hover:bg-slate-700 border border-transparent'
                                            }`}
                                    >
                                        <div className="flex justify-between items-center">
                                            <span className="font-medium text-slate-200 capitalize">
                                                {commodity.commodity}
                                            </span>
                                            <span className="text-xs text-slate-400">
                                                {formatFileSize(commodity.file_size_mb)}
                                            </span>
                                        </div>
                                        <div className="text-xs text-slate-500 mt-1">
                                            Updated: {new Date(commodity.last_updated).toLocaleDateString()}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Price Chart */}
                <div className="lg:col-span-2">
                    <div className="card h-full">
                        {selectedCommodity ? (
                            <>
                                <div className="flex justify-between items-center mb-4">
                                    <h2 className="text-xl font-semibold text-slate-100 capitalize">
                                        {selectedCommodity} Price History
                                    </h2>
                                    <Link
                                        to={`/commodity/${selectedCommodity}`}
                                        className="text-sm text-emerald-400 hover:text-emerald-300"
                                    >
                                        View Details →
                                    </Link>
                                </div>

                                {priceData.length > 0 ? (
                                    <div className="h-[400px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={priceData}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                                <XAxis
                                                    dataKey="year"
                                                    stroke="#9CA3AF"
                                                    tick={{ fill: '#9CA3AF' }}
                                                />
                                                <YAxis
                                                    stroke="#9CA3AF"
                                                    tick={{ fill: '#9CA3AF' }}
                                                    tickFormatter={(value) => value.toLocaleString()}
                                                />
                                                <Tooltip
                                                    contentStyle={{
                                                        backgroundColor: '#1E293B',
                                                        border: '1px solid #374151',
                                                        borderRadius: '8px'
                                                    }}
                                                    labelStyle={{ color: '#F1F5F9' }}
                                                    formatter={(value: number) => [value.toLocaleString(), 'Value']}
                                                />
                                                <Line
                                                    type="monotone"
                                                    dataKey="price"
                                                    stroke="#10B981"
                                                    strokeWidth={2}
                                                    dot={false}
                                                    activeDot={{ r: 6, fill: '#10B981' }}
                                                />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                ) : (
                                    <div className="h-[400px] flex items-center justify-center text-slate-400">
                                        Loading price data...
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="h-[400px] flex flex-col items-center justify-center text-slate-400">
                                <BarChart3 className="w-16 h-16 mb-4 text-slate-600" />
                                <p className="text-lg">Select a commodity to view price history</p>
                                <p className="text-sm mt-2">Click on any commodity in the list to see its historical prices</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
