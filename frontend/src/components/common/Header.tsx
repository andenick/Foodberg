import { BarChart3, ChefHat, Database, Globe, History, TrendingUp } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'

export default function Header() {
    const location = useLocation()

    const navItems = [
        { path: '/index', label: 'Food Index', icon: BarChart3 },
        { path: '/explore', label: 'Price Explorer', icon: TrendingUp },
        { path: '/geographic', label: 'Geographic', icon: Globe },
        { path: '/trends', label: 'Historical Trends', icon: History },
        { path: '/sources', label: 'Data Sources', icon: Database },
    ]

    return (
        <header className="bg-slate-800/90 backdrop-blur-sm shadow-lg border-b border-slate-700 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center py-4">
                    <Link to="/" className="flex items-center space-x-3 group">
                        <ChefHat className="w-8 h-8 text-emerald-500 group-hover:text-emerald-400 transition-colors" />
                        <div>
                            <h1 className="text-2xl font-bold text-emerald-400 group-hover:text-emerald-300 transition-colors">
                                Foodberg
                            </h1>
                            <p className="text-xs text-slate-400 hidden sm:block">Historical Food Price Explorer</p>
                        </div>
                    </Link>

                    <nav className="hidden md:flex items-center space-x-1">
                        {navItems.map((item) => {
                            const Icon = item.icon
                            const isActive = location.pathname === item.path
                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${isActive
                                        ? 'bg-emerald-600/20 text-emerald-400'
                                        : 'text-slate-300 hover:bg-slate-700 hover:text-slate-100'
                                        }`}
                                >
                                    <Icon className="w-4 h-4" />
                                    <span className="text-sm font-medium">{item.label}</span>
                                </Link>
                            )
                        })}
                    </nav>
                </div>
            </div>
        </header>
    )
}
