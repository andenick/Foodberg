import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
// Foodberg's own Tailwind styles first; the Arcanum Site Kit chrome styles after
// so the .ark-* header/footer always win, while the app's content keeps its own
// (explicit-class) Tailwind styling. The 2-line theme overrides --ark-accent.
import './index.css'
import './arcanum/arcanum.css'
import './arcanum/foodberg-theme.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <BrowserRouter>
            <App />
        </BrowserRouter>
    </React.StrictMode>,
)

