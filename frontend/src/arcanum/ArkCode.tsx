// =============================================================================
// Arcanum Site Kit — ArkCode.tsx (React/TS parity port of ark-code.js v1.0)
//
// CONTENT_RENDERING_STANDARD §3: every code chunk is a visible bordered box
// (.ark-code) with a copy button (.ark-copy) and an R | Python toggle, and the
// script is downloadable as a runnable .R / .py file — not just readable.
//
// The kit implements this as a vanilla-JS DOM enhancer that self-initializes on
// DOMContentLoaded and rewrites `.ark-code[data-arkcode]` markup in place. That
// cannot work here: Foodberg is a React SPA whose code boxes mount after
// DOMContentLoaded and re-render on state change, so the enhancer would either
// never fire or fight React for ownership of the DOM. This is the contract-
// faithful port — same class names, same button order, same localStorage key
// ("ark-code-lang", so a reader who picks Python on one Arcanum site keeps
// Python here), same download-stem rules. Any fix to the toggle behaviour here
// should be mirrored back into ark-code.js and vice versa.
//
// The .ark-code / .ark-code-head / .ark-copy CSS is already vendored in
// arcanum.css §12 and is reused unchanged; only the toggle chrome (which §12
// does not carry) is styled locally with the site's Tailwind tokens.
// =============================================================================
import { useCallback, useEffect, useRef, useState } from 'react'

export type CodeLang = 'r' | 'python'

export interface CodeSource {
    lang: CodeLang
    code: string
}

const NICE: Record<CodeLang, string> = { r: 'R', python: 'Python' }
const EXT: Record<CodeLang, string> = { r: 'R', python: 'py' }

// The kit's key, deliberately. Language choice is a reader preference, not a
// per-page setting.
const STORE_KEY = 'ark-code-lang'

function readPref(): string {
    try {
        return window.localStorage.getItem(STORE_KEY) || ''
    } catch {
        // Private browsing / storage disabled. A missing preference is not an
        // error — it just means "use the declared default".
        return ''
    }
}

function writePref(lang: string): void {
    try {
        window.localStorage.setItem(STORE_KEY, lang)
    } catch {
        /* nothing to do: the toggle still works for this page view */
    }
}

export interface ArkCodeProps {
    /** One entry per language. Both R and Python are required by §3. */
    sources: CodeSource[]
    /** Download stem, no extension — ".R" / ".py" is appended per language. */
    filename: string
    /** Shown in the box head, e.g. a file path or a one-line description. */
    path?: string
    /** Which language shows first. Omit to honour the reader's saved choice. */
    defaultLang?: CodeLang
    /** Stable public URLs for the same scripts, listed under the box. */
    stableUrls?: Partial<Record<CodeLang, string>>
}

export default function ArkCode({
    sources, filename, path, defaultLang, stableUrls,
}: ArkCodeProps) {
    const [lang, setLang] = useState<CodeLang>(() => {
        const wanted = (defaultLang ?? readPref()) as CodeLang
        return sources.some(s => s.lang === wanted) ? wanted : (sources[0]?.lang ?? 'python')
    })
    const [copied, setCopied] = useState(false)
    const timer = useRef<number | null>(null)

    useEffect(() => () => {
        if (timer.current) window.clearTimeout(timer.current)
    }, [])

    const active = sources.find(s => s.lang === lang) ?? sources[0]

    const copy = useCallback(() => {
        if (!active) return
        const done = () => {
            setCopied(true)
            if (timer.current) window.clearTimeout(timer.current)
            timer.current = window.setTimeout(() => setCopied(false), 1200)
        }
        // execCommand is deprecated but is the only clipboard path on a page
        // served without a secure context; failing silently would leave the
        // button looking broken.
        const fallback = () => {
            const ta = document.createElement('textarea')
            ta.value = active.code
            ta.style.position = 'fixed'
            ta.style.opacity = '0'
            document.body.appendChild(ta)
            ta.focus()
            ta.select()
            try {
                document.execCommand('copy')
                done()
            } catch {
                /* clipboard unavailable — the code is still selectable by hand */
            }
            ta.remove()
        }
        if (navigator.clipboard?.writeText) {
            navigator.clipboard.writeText(active.code).then(done, fallback)
        } else {
            fallback()
        }
    }, [active])

    const download = useCallback(() => {
        if (!active) return
        // Downloads exactly the text on screen, so the file can never drift
        // from the snippet the reader just read.
        const blob = new Blob([active.code], { type: 'text/plain;charset=utf-8' })
        const a = document.createElement('a')
        a.href = URL.createObjectURL(blob)
        a.download = `${filename}.${EXT[active.lang]}`
        document.body.appendChild(a)
        a.click()
        setTimeout(() => { URL.revokeObjectURL(a.href); a.remove() }, 0)
    }, [active, filename])

    if (!sources.length || !active) return null
    const multi = sources.length > 1

    return (
        <div>
            <div className="ark-code">
                <div className="ark-code-head">
                    {multi && (
                        <div
                            className="flex gap-1"
                            role="tablist"
                            aria-label="Code language"
                        >
                            {sources.map(s => {
                                const on = s.lang === active.lang
                                return (
                                    <button
                                        key={s.lang}
                                        type="button"
                                        role="tab"
                                        aria-selected={on}
                                        onClick={() => { setLang(s.lang); writePref(s.lang) }}
                                        className={`px-2.5 py-0.5 rounded border text-[0.74rem] font-medium transition-colors ${on
                                            ? 'bg-emerald-600 border-emerald-600 text-white'
                                            : 'bg-ark-bg-soft border-ark-line text-ark-fg-dim hover:text-ark-fg'
                                            }`}
                                    >
                                        {NICE[s.lang]}
                                    </button>
                                )
                            })}
                        </div>
                    )}
                    {path && <span className="ark-code-path">{path}</span>}
                    {/* .ark-copy carries margin-left:auto in arcanum.css §12, so
                        the control pair sits hard right of the head. */}
                    <button type="button" className="ark-copy" onClick={copy} disabled={copied}>
                        {copied ? 'Copied' : 'Copy'}
                    </button>
                    <button type="button" className="ark-copy" onClick={download}>
                        Download .{EXT[active.lang]}
                    </button>
                </div>
                <pre>
                    <code>{active.code}</code>
                </pre>
            </div>

            {stableUrls && Object.keys(stableUrls).length > 0 && (
                <p className="text-xs text-ark-fg-dim -mt-2 mb-4">
                    Stable links to the same two scripts:{' '}
                    {(Object.keys(stableUrls) as CodeLang[])
                        .filter(l => stableUrls[l])
                        .map((l, i) => (
                            <span key={l}>
                                {i > 0 ? ' · ' : ''}
                                <a
                                    className="text-emerald-400 hover:text-emerald-300"
                                    href={stableUrls[l]}
                                    download=""
                                >
                                    {filename}.{EXT[l]}
                                </a>
                            </span>
                        ))}
                </p>
            )}
        </div>
    )
}
