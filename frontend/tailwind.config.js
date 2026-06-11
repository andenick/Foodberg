/** @type {import('tailwindcss').Config} */
export default {
    // Theme is switched by toggling the `.dark` class on <html> (in tandem with
    // the kit `data-theme` attribute that drives the --ark-* tokens). See the
    // toggle in src/arcanum/ArcanumChrome.tsx and the no-FOUC script in index.html.
    darkMode: 'class',
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Foodberg brand colors - kitchen-optimized dark theme
                'foodberg': {
                    50: '#f0fdf4',
                    100: '#dcfce7',
                    200: '#bbf7d0',
                    300: '#86efac',
                    400: '#4ade80',
                    500: '#22c55e',
                    600: '#16a34a',
                    700: '#15803d',
                    800: '#166534',
                    900: '#14532d',
                },
                // Arcanum Site Kit semantic tokens — map the kit --ark-* CSS vars
                // into Tailwind so `text-ark-fg`, `bg-ark-bg-soft`, `border-ark-line`
                // etc. flip automatically with the light/dark toggle (the vars are
                // redefined under :root[data-theme] in arcanum.css).
                'ark': {
                    'bg': 'var(--ark-bg)',
                    'bg-soft': 'var(--ark-bg-soft)',
                    'fg': 'var(--ark-fg)',
                    'fg-dim': 'var(--ark-fg-dim)',
                    'line': 'var(--ark-line)',
                    'tag': 'var(--ark-tag)',
                    'accent': 'var(--ark-accent)',
                },
            },
        },
    },
    plugins: [],
}

