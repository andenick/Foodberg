import { Globe, MapPin } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../services/api'
import {
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis
} from 'recharts'

// Color palette for multiple lines
const COLORS = [
    '#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
]

export default function GeographicPrices() {
    const [selectedCommodity, setSelectedCommodity] = useState('wheat')
    const [selectedRegions, setSelectedRegions] = useState<string[]>(['United States', 'China', 'Brazil'])
    const [priceData, setPriceData] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [availableCountries, setAvailableCountries] = useState<string[]>([])

    const commodities = [
        'wheat', 'corn', 'rice', 'soybeans', 'cotton', 'cattle', 'milk'
    ]

    useEffect(() => {
        loadGeographicData()
    }, [selectedCommodity])

    const loadGeographicData = async () => {
        setLoading(true)
        try {
            const response = await api.getWASDEData(selectedCommodity, 5000)
            const result = response.data
            const records = result.data || []

            const locations = [...new Set(records.map((r: any) => r.location).filter(Boolean))]
            setAvailableCountries(locations as string[])

            const locationData: { [key: string]: { [year: number]: number[] } } = {}

            records.forEach((record: any) => {
                if (!record.location || record.numeric_value === null) return

                if (!locationData[record.location]) {
                    locationData[record.location] = {}
                }
                if (!locationData[record.location][record.year]) {
                    locationData[record.location][record.year] = []
                }
                locationData[record.location][record.year].push(record.numeric_value)
            })

            const years = [...new Set(records.map((r: any) => r.year))].sort() as number[]
            const chartData = years.map((year: number) => {
                const point: any = { year }
                selectedRegions.forEach(region => {
                    if (locationData[region] && locationData[region][year]) {
                        const values = locationData[region][year]
                        point[region] = values.reduce((a: number, b: number) => a + b, 0) / values.length
                    }
                })
                return point
            })

            setPriceData(chartData.filter(d => Object.keys(d).length > 1))
        } catch (error) {
            console.error('Failed to load geographic data:', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (availableCountries.length > 0) {
            loadGeographicData()
        }
    }, [selectedRegions])

    const toggleRegion = (region: string) => {
        if (selectedRegions.includes(region)) {
            setSelectedRegions(selectedRegions.filter(r => r !== region))
        } else if (selectedRegions.length < 6) {
            setSelectedRegions([...selectedRegions, region])
        }
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-slate-100 mb-2 flex items-center">
                    <Globe className="w-8 h-8 mr-3 text-blue-400" />
                    Geographic Price Comparison
                </h1>
                <p className="text-slate-400">
                    Compare food commodity prices across different regions and countries
                </p>
            </div>

            <div className="card mb-6">
                <h2 className="text-lg font-semibold text-slate-100 mb-4">Select Commodity</h2>
                <div className="flex flex-wrap gap-2">
                    {commodities.map(commodity => (
                        <button
                            key={commodity}
                            onClick={() => setSelectedCommodity(commodity)}
                            className={`px-4 py-2 rounded-lg font-medium capitalize transition-colors ${selectedCommodity === commodity
                                    ? 'bg-emerald-600 text-white'
                                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                }`}
                        >
                            {commodity}
                        </button>
                    ))}
                </div>
            </div>

            <div className="card mb-6">
                <h2 className="text-lg font-semibold text-slate-100 mb-4">
                    Select Regions to Compare (max 6)
                    <span className="text-sm text-slate-400 ml-2">
                        ({selectedRegions.length}/6 selected)
                    </span>
                </h2>

                {availableCountries.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                        {availableCountries.slice(0, 20).map((country) => (
                            <button
                                key={country}
                                onClick={() => toggleRegion(country)}
                                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center ${selectedRegions.includes(country)
                                        ? 'text-white'
                                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                    }`}
                                style={selectedRegions.includes(country) ? {
                                    backgroundColor: COLORS[selectedRegions.indexOf(country) % COLORS.length]
                                } : {}}
                                disabled={!selectedRegions.includes(country) && selectedRegions.length >= 6}
                            >
                                <MapPin className="w-3 h-3 mr-1" />
                                {country}
                            </button>
                        ))}
                    </div>
                ) : (
                    <p className="text-slate-400">Loading available regions...</p>
                )}
            </div>

            <div className="card">
                <h2 className="text-xl font-semibold text-slate-100 mb-4 capitalize">
                    {selectedCommodity} Prices by Region
                </h2>

                {loading ? (
                    <div className="h-[500px] flex items-center justify-center">
                        <div className="text-center">
                            <div className="animate-spin w-12 h-12 border-2 border-emerald-400 border-t-transparent rounded-full mx-auto"></div>
                            <p className="text-slate-400 mt-4">Loading price data...</p>
                        </div>
                    </div>
                ) : priceData.length > 0 ? (
                    <div className="h-[500px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={priceData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                <XAxis dataKey="year" stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} />
                                <YAxis stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} tickFormatter={(value) => value.toLocaleString()} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #374151', borderRadius: '8px' }}
                                    labelStyle={{ color: '#F1F5F9' }}
                                    formatter={(value: number, name: string) => [value.toLocaleString(undefined, { maximumFractionDigits: 2 }), name]}
                                />
                                <Legend />
                                {selectedRegions.map((region, index) => (
                                    <Line
                                        key={region}
                                        type="monotone"
                                        dataKey={region}
                                        stroke={COLORS[index % COLORS.length]}
                                        strokeWidth={2}
                                        dot={false}
                                        activeDot={{ r: 6 }}
                                    />
                                ))}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                ) : (
                    <div className="h-[500px] flex items-center justify-center text-slate-400">
                        <div className="text-center">
                            <Globe className="w-16 h-16 mx-auto mb-4 text-slate-600" />
                            <p>No regional data available for this commodity.</p>
                            <p className="text-sm mt-2">Try selecting a different commodity.</p>
                        </div>
                    </div>
                )}
            </div>

            {priceData.length > 0 && selectedRegions.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                    {selectedRegions.map((region, index) => {
                        const regionData = priceData.filter(d => d[region] !== undefined)
                        const latestValue = regionData.length > 0 ? regionData[regionData.length - 1][region] : null
                        const firstValue = regionData.length > 0 ? regionData[0][region] : null
                        const change = firstValue && latestValue ? ((latestValue - firstValue) / firstValue * 100) : null

                        return (
                            <div
                                key={region}
                                className="card"
                                style={{ borderLeftColor: COLORS[index % COLORS.length], borderLeftWidth: '4px' }}
                            >
                                <h3 className="font-semibold text-slate-200">{region}</h3>
                                <div className="text-2xl font-bold text-slate-100 mt-2">
                                    {latestValue ? latestValue.toLocaleString(undefined, { maximumFractionDigits: 2 }) : 'N/A'}
                                </div>
                                {change !== null && (
                                    <div className={`text-sm mt-1 ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                        {change >= 0 ? '+' : ''}{change.toFixed(1)}% over period
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
