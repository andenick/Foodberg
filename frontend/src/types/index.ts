export interface CommodityData {
    commodity: string
    currentPrice: number
    priceChange: number
    priceChangePercent: number
    lastUpdated: string
    unit: string
    category: string
    source: string
    high?: number
    low?: number
    volume?: number
}

export interface RecipeIngredient {
    id: string
    name: string
    quantity: number
    unit: string
    pricePerUnit: number
    category: string
    cost: number
    yieldPercent?: number
    preparation?: string
}

export interface Recipe {
    id: string
    name: string
    servings: number
    ingredients: RecipeIngredient[]
    laborMinutes?: number
    laborRate?: number
    overheadPercent?: number
    targetFoodCostPercent?: number
    totalCost: number
    costPerServing: number
    createdAt: string
}

export interface MenuItem {
    id: string
    name: string
    menuPrice: number
    cost: number
    profit: number
    unitsSold: number
    classification?: 'STAR' | 'PUZZLE' | 'PLOW HORSE' | 'DOG'
}

export interface PriceAlert {
    id: string
    commodity: string
    threshold: number
    direction: 'up' | 'down'
    comparison: 'percent' | 'absolute'
    active: boolean
    createdAt: string
    lastTriggered?: string
    notificationMethod?: 'email' | 'sms' | 'push'
}

export interface HistoricalPrice {
    date: string
    price: number
    volume?: number
    high?: number
    low?: number
}

export interface VendorPrice {
    vendor: string
    price: number
    unit: string
    minimumOrder?: number
    deliveryFee?: number
    deliveryTime?: string
    lastUpdated: string
}

export interface SeasonalData {
    month: number
    commodity: string
    avgPrice: number
    availability: 'peak' | 'available' | 'limited' | 'unavailable'
    forecast?: number
}

export interface Substitution {
    original: string
    substitute: string
    costDifference: number
    nutritionScore: number
    tasteScore: number
    availability: string
    reason: string
}

