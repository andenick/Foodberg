import { ArrowDown, ArrowUp, BarChart3, Minus } from 'lucide-react'
import { useEffect, useState } from 'react'
import {
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis
} from 'recharts'
import { api } from '../services/api'
import { downloadCsv, useArkTheme } from '../arcanum/arkChartTheme'
import { ChartMetaStrip, ScrollableDataTable } from '../components/ChartDetails'
import GlobalIndices from '../components/GlobalIndices'

const COLORS: Record<string, string> = {
    fao_overall: '#10B981',
    fao_meat: '#EF4444',
    fao_dairy: '#3B82F6',
    fao_cereals: '#F59E0B',
    fao_oils: '#8B5CF6',
    fao_sugar: '#EC4899',
    bls_overall: '#06B6D4',
}

const CATEGORY_LABELS: Record<string, string> = {
    fao_overall: 'FAO Overall',
    fao_meat: 'Meat',
    fao_dairy: 'Dairy',
    fao_cereals: 'Cereals',
    fao_oils: 'Vegetable Oils',
    fao_sugar: 'Sugar',
    bls_overall: 'US CPI Food',
}

const FAO_CATEGORIES = ['fao_meat', 'fao_dairy', 'fao_cereals', 'fao_oils', 'fao_sugar']

interface IndexSummary {
    category: string
    index_value: number
    date: string
    components: Record<string, number> | null
}

export default function FoodPriceIndex() {
    const [indices, setIndices] = useState<IndexSummary[]>([])
    const [chartData, setChartData] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [selectedCategories, setSelectedCategories] = useState<string[]>(['fao_overall', 'bls_overall'])
    const [timeRange, setTimeRange] = useState<string>('10y')
    const t = useArkTheme()

    useEffect(() => {
        loadIndices()
    }, [])

    useEffect(() => {
        loadChartData()
    }, [selectedCategories, timeRange])

    const loadIndices = async () => {
        try {
            const response = await api.getCompositeIndices()
            setIndices(response.data.indices || [])
        } catch (error) {
            console.error('Failed to load indices:', error)
        } finally {
            setLoading(false)
        }
    }

    const loadChartData = async () => {
        if (selectedCategories.length === 0) {
            setChartData([])
            return
        }

        try {
            const promises = selectedCategories.map(async (category) => {
                const response = await api.getCompositeIndex(category)
                return { category, data: response.data.data || [] }
            })

            const results = await Promise.all(promises)

            // Combine by date
            const dateMap: Record<string, any> = {}
            results.forEach(({ category, data }) => {
                data.forEach((point: any) => {
                    const dateKey = point.date?.substring(0, 7) || ''
                    if (!dateMap[dateKey]) {
                        dateMap[dateKey] = { date: dateKey }
                    }
                    dateMap[dateKey][category] = point.index_value
                })
            })

            let combined = Object.values(dateMap).sort((a: any, b: any) =>
                a.date.localeCompare(b.date)
            )

            // Apply time range filter
            const cutoff = getTimeCutoff(timeRange)
            if (cutoff) {
                combined = combined.filter((d: any) => d.date >= cutoff)
            }

            setChartData(combined)
        } catch (error) {
            console.error('Failed to load chart data:', error)
        }
    }

    const getTimeCutoff = (range: string): string | null => {
        const now = new Date()
        switch (range) {
            case '5y': return `${now.getFullYear() - 5}-${String(now.getMonth() + 1).padStart(2, '0')}`
            case '10y': return `${now.getFullYear() - 10}-${String(now.getMonth() + 1).padStart(2, '0')}`
            case '20y': return `${now.getFullYear() - 20}-${String(now.getMonth() + 1).padStart(2, '0')}`
            case 'all': return null
            default: return null
        }
    }

    const toggleCategory = (category: string) => {
        setSelectedCategories(prev =>
            prev.includes(category)
                ? prev.filter(c => c !== category)
                : [...prev, category]
        )
    }

    const getLatestValue = (category: string): IndexSummary | undefined => {
        return indices.find(i => i.category === category)
    }

    const getChangeIndicator = (value: number, baseValue = 100) => {
        const change = ((value - baseValue) / baseValue) * 100
        if (change > 1) return { icon: ArrowUp, color: 'text-red-400', text: `+${change.toFixed(1)}%` }
        if (change < -1) return { icon: ArrowDown, color: 'text-green-400', text: `${change.toFixed(1)}%` }
        return { icon: Minus, color: 'text-ark-fg-dim', text: `${change.toFixed(1)}%` }
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-ark-fg mb-2">Food Price Index</h1>
                <p className="text-ark-fg-dim">
                    Composite food price indices based on FAO global data and US BLS CPI components
                </p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-8">
                {['fao_overall', ...FAO_CATEGORIES, 'bls_overall'].map(category => {
                    const latest = getLatestValue(category)
                    const value = latest?.index_value ?? 0
                    const baseVal = category.startsWith('bls') ? 250 : 100
                    const indicator = getChangeIndicator(value, baseVal)
                    const Icon = indicator.icon
                    const isSelected = selectedCategories.includes(category)

                    return (
                        <button
                            key={category}
                            onClick={() => toggleCategory(category)}
                            className={`p-3 rounded-lg text-left transition-all ${isSelected
                                    ? 'bg-ark-tag border-2'
                                    : 'bg-ark-bg-soft border border-ark-line opacity-60 hover:opacity-100'
                                }`}
                            style={{ borderColor: isSelected ? COLORS[category] : undefined }}
                        >
                            <div className="text-xs text-ark-fg-dim mb-1">{CATEGORY_LABELS[category]}</div>
                            <div className="text-lg font-bold text-ark-fg">{value.toFixed(1)}</div>
                            <div className={`flex items-center text-xs ${indicator.color}`}>
                                <Icon className="w-3 h-3 mr-1" />
                                {indicator.text}
                            </div>
                            {latest?.date && (
                                <div className="text-[10px] text-ark-fg-dim mt-1">
                                    {latest.date.substring(0, 7)}
                                </div>
                            )}
                        </button>
                    )
                })}
            </div>

            {/* Time Range Selector */}
            <div className="flex gap-2 mb-6">
                {['5y', '10y', '20y', 'all'].map(range => (
                    <button
                        key={range}
                        onClick={() => setTimeRange(range)}
                        className={`px-4 py-2 rounded-lg font-medium transition-colors ${timeRange === range
                                ? 'bg-emerald-600 text-white'
                                : 'bg-ark-tag text-ark-fg-dim hover:bg-ark-line'
                            }`}
                    >
                        {range === 'all' ? 'All Time' : range.toUpperCase()}
                    </button>
                ))}
            </div>

            {/* Main Chart */}
            <div className="card mb-8">
                <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
                    <h2 className="text-xl font-semibold text-ark-fg flex items-center">
                        <BarChart3 className="w-5 h-5 mr-2 text-emerald-400" />
                        Food Price Indices Over Time
                    </h2>
                    <button
                        type="button"
                        className="ark-btn ark-btn-sm ark-btn-ghost"
                        onClick={() => downloadCsv(chartData, 'foodberg_food_price_indices')}
                        disabled={chartData.length === 0}
                    >
                        Download CSV
                    </button>
                </div>

                {loading ? (
                    <div className="h-[500px] flex items-center justify-center">
                        <div className="animate-spin w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full"></div>
                    </div>
                ) : chartData.length > 0 ? (
                    <div className="h-[500px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke={t.gridStroke} />
                                <XAxis
                                    dataKey="date"
                                    stroke={t.axisStroke}
                                    tick={{ fill: t.dim, fontSize: 12 }}
                                    tickFormatter={(v) => v.substring(0, 4)}
                                    interval="preserveStartEnd"
                                />
                                <YAxis
                                    stroke={t.axisStroke}
                                    tick={{ fill: t.dim }}
                                />
                                <Tooltip
                                    contentStyle={t.tooltip}
                                    labelStyle={{ color: t.fg }}
                                    formatter={(value: number, name: string) => [
                                        value.toFixed(1),
                                        CATEGORY_LABELS[name] || name
                                    ]}
                                />
                                <Legend
                                    formatter={(value: string) => CATEGORY_LABELS[value] || value}
                                />
                                {selectedCategories.map(category => (
                                    <Line
                                        key={category}
                                        type="monotone"
                                        dataKey={category}
                                        stroke={COLORS[category]}
                                        strokeWidth={category.includes('overall') ? 3 : 1.5}
                                        dot={false}
                                        connectNulls
                                    />
                                ))}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                ) : (
                    <div className="h-[500px] flex items-center justify-center text-ark-fg-dim">
                        Select indices above to compare
                    </div>
                )}

                {chartData.length > 0 && (
                    <>
                        <ChartMetaStrip
                            meta={{
                                source: 'FAO Food Price Index + US BLS CPI components (local dataset, offline)',
                                unit: 'Index (FAO base 2014-2016 = 100 · BLS base 1982-84 = 100)',
                                dateRange: `${chartData[0].date} → ${chartData[chartData.length - 1].date}`,
                                points: chartData.length,
                                note: 'Monthly observations. FAO and BLS indices use different base periods — compare shapes, not levels.',
                            }}
                        />
                        <ScrollableDataTable
                            rows={chartData}
                            columns={[
                                { key: 'date', label: 'Month' },
                                ...selectedCategories.map(c => ({ key: c, label: CATEGORY_LABELS[c] || c, numeric: true })),
                            ]}
                            filename="foodberg_food_price_indices"
                        />
                    </>
                )}
            </div>

            {/* Global index families (Pink Sheet world indices + FAO country food CPIs) */}
            <GlobalIndices />

            {/* Methodology Note */}
            <div className="card bg-ark-bg-soft mt-8">
                <h3 className="text-lg font-semibold text-ark-fg mb-3">About These Indices</h3>
                <div className="grid md:grid-cols-2 gap-4 text-sm text-ark-fg-dim">
                    <div>
                        <h4 className="text-ark-fg-dim font-medium mb-1">FAO Food Price Index</h4>
                        <p>
                            Global index tracking international prices of 5 food commodity groups.
                            Base period: 2014-2016 = 100. Weights: Meat 34.8%, Cereals 27.2%,
                            Dairy 17.3%, Vegetable Oils 13.5%, Sugar 7.2%.
                        </p>
                    </div>
                    <div>
                        <h4 className="text-ark-fg-dim font-medium mb-1">US CPI Food (BLS)</h4>
                        <p>
                            US consumer price index for food, computed from BLS sub-components:
                            Meats/Poultry/Fish/Eggs 30%, Cereals/Bakery 20%, Fruits/Vegetables 18%,
                            Food Away from Home 17%, Dairy 15%. Base: 1982-84 = 100.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
