export default function Footer() {
    return (
        <footer className="bg-slate-800/50 border-t border-slate-700 mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div>
                        <h3 className="text-lg font-semibold text-slate-100 mb-4">Foodberg</h3>
                        <p className="text-sm text-slate-400">
                            Professional food cost management platform for chefs and culinary professionals.
                            Save money, optimize menus, and run a more profitable kitchen.
                        </p>
                    </div>

                    <div>
                        <h3 className="text-lg font-semibold text-slate-100 mb-4">Data Sources</h3>
                        <ul className="space-y-2 text-sm text-slate-400">
                            <li>USDA Market News</li>
                            <li>Federal Reserve Economic Data</li>
                            <li>FAO Food Prices</li>
                            <li>World Bank Commodities</li>
                        </ul>
                    </div>

                    <div>
                        <h3 className="text-lg font-semibold text-slate-100 mb-4">Resources</h3>
                        <ul className="space-y-2 text-sm text-slate-400">
                            <li><a href="#" className="hover:text-emerald-400 transition-colors">Documentation</a></li>
                            <li><a href="#" className="hover:text-emerald-400 transition-colors">API Reference</a></li>
                            <li><a href="#" className="hover:text-emerald-400 transition-colors">Support</a></li>
                            <li><a href="#" className="hover:text-emerald-400 transition-colors">Privacy Policy</a></li>
                        </ul>
                    </div>
                </div>

                <div className="mt-8 pt-8 border-t border-slate-700 text-center text-sm text-slate-500">
                    <p>&copy; {new Date().getFullYear()} Foodberg. Professional kitchen cost management.</p>
                </div>
            </div>
        </footer>
    )
}

