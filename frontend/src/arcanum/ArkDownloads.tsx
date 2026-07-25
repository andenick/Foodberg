// =============================================================================
// Arcanum Site Kit — ArkDownloads.tsx (React/TS parity port of ark-downloads.js v1.1)
//
// ONE download-row renderer for every chart and every table on the site, so
// DOWNLOAD_AND_FORMATS_STANDARD rules 1 and 2 (CSV / XLSX / Parquet on every
// data surface, JSON never) are true by construction rather than by per-page
// discipline. Mirrors the kit's `ArkDownloads.buttons()` / `.csvButton()` API,
// its .ark-download / .ark-btn markup, and its ORDER, so the vendored CSS
// applies unchanged.
//
// JSON is deliberately absent and is filtered out even if a caller passes it —
// that is the standard, not an oversight.
// =============================================================================
import { downloadCsv } from './arkChartTheme'

export type DownloadFormat = 'csv' | 'xlsx' | 'parquet' | 'bundle' | 'zip'

const LABEL: Record<string, string> = {
    csv: 'CSV', xlsx: 'XLSX', parquet: 'Parquet', bundle: 'Bundle (.zip)', zip: '.zip',
}
const ORDER: string[] = ['csv', 'xlsx', 'parquet', 'bundle', 'zip']

export interface ArkDownloadsProps {
    /** format -> href. A falsy href renders nothing for that format. */
    hrefs?: Partial<Record<DownloadFormat, string | undefined | null>>
    /** In-memory rows for a client-side CSV, when there is no CSV endpoint. */
    rows?: Array<Record<string, unknown>>
    /** Download stem, no extension. */
    filename: string
    /** Row label; pass null to omit it. */
    label?: string | null
    /** Explain, honestly and visibly, why a format is missing (e.g. XLSX row limits). */
    unavailable?: Partial<Record<DownloadFormat, string>>
    className?: string
}

/**
 * The uniform download row.
 *
 * Where a format genuinely cannot be produced (Foodberg's `wasde` table exceeds
 * Excel's 1,048,576-row worksheet limit outright), pass `unavailable` and the
 * row says so in words instead of silently offering two formats where the
 * standard asks for three. A stated limit is compliance; a missing button is a
 * defect.
 */
export default function ArkDownloads({
    hrefs, rows, filename, label = 'Download:', unavailable, className,
}: ArkDownloadsProps) {
    const keys = Object.keys(hrefs ?? {})
        .filter(k => k !== 'json' && (hrefs as Record<string, string>)?.[k])
        .sort((a, b) => {
            const ia = ORDER.indexOf(a), ib = ORDER.indexOf(b)
            return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib)
        })

    const notes = Object.entries(unavailable ?? {}).filter(([, v]) => !!v)
    if (!keys.length && !rows?.length && !notes.length) return null

    return (
        <div className={`ark-download${className ? ` ${className}` : ''}`}>
            {label ? <span className="ark-download-label">{label}</span> : null}

            {/* Client-side CSV from the exact rows that were plotted. */}
            {rows?.length ? (
                <button
                    type="button"
                    className="ark-btn ark-btn-sm"
                    onClick={() => downloadCsv(rows, filename)}
                >
                    CSV
                </button>
            ) : null}

            {keys.map(k => (
                <a
                    key={k}
                    className="ark-btn ark-btn-sm"
                    href={(hrefs as Record<string, string>)[k]}
                    download=""
                >
                    {LABEL[k] ?? k.toUpperCase()}
                </a>
            ))}

            {notes.map(([k, why]) => (
                <span key={k} className="text-xs text-ark-fg-dim px-2" title={String(why)}>
                    {LABEL[k] ?? k.toUpperCase()} unavailable — {String(why)}
                </span>
            ))}
        </div>
    )
}
