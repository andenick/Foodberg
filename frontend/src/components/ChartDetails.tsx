import { downloadCsv } from '../arcanum/arkChartTheme'

/* ChartDetails — the standard "what am I looking at" block under every chart:
   a meta strip (source, unit, range, observation count, latest value) and a
   scrollable table of the exact plotted observations with a CSV download.
   Real data only: render it with the same rows the chart was drawn from. */

export interface ChartMeta {
    source?: string | null
    unit?: string | null
    dateRange?: string | null
    points?: number
    latestLabel?: string | null
    latestValue?: string | null
    note?: string | null
}

export function ChartMetaStrip({ meta }: { meta: ChartMeta }) {
    const items: Array<[string, string]> = []
    if (meta.source) items.push(['Source', meta.source])
    if (meta.unit) items.push(['Unit', meta.unit])
    if (meta.dateRange) items.push(['Range', meta.dateRange])
    if (meta.points !== undefined) items.push(['Observations', meta.points.toLocaleString()])
    if (meta.latestValue) items.push([meta.latestLabel || 'Latest', meta.latestValue])
    return (
        <div className="mt-4 pt-4 border-t border-ark-line">
            <div className="flex flex-wrap gap-x-8 gap-y-2 text-sm">
                {items.map(([k, v]) => (
                    <div key={k}>
                        <span className="text-ark-fg-dim">{k}: </span>
                        <span className="text-ark-fg font-medium">{v}</span>
                    </div>
                ))}
            </div>
            {meta.note ? <p className="text-xs text-ark-fg-dim mt-2">{meta.note}</p> : null}
        </div>
    )
}

export function ScrollableDataTable({
    rows,
    columns,
    filename,
    maxHeight = 320,
}: {
    rows: Array<Record<string, unknown>>
    columns: Array<{ key: string; label: string; numeric?: boolean }>
    filename: string
    maxHeight?: number
}) {
    if (!rows.length) return null
    const fmt = (v: unknown, numeric?: boolean) => {
        if (v === null || v === undefined) return '—'
        if (numeric && typeof v === 'number')
            return v.toLocaleString(undefined, { maximumFractionDigits: 2 })
        return String(v)
    }
    return (
        <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-ark-fg-dim uppercase tracking-wide">
                    Plotted data ({rows.length.toLocaleString()} rows)
                </h3>
                <button
                    type="button"
                    className="ark-btn ark-btn-sm ark-btn-ghost"
                    onClick={() => downloadCsv(rows, filename)}
                >
                    Download CSV
                </button>
            </div>
            <div
                className="overflow-y-auto overflow-x-auto border border-ark-line rounded-lg"
                style={{ maxHeight }}
            >
                <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-ark-tag">
                        <tr>
                            {columns.map((c) => (
                                <th
                                    key={c.key}
                                    className={`p-2 text-ark-fg-dim font-semibold text-xs uppercase tracking-wide ${c.numeric ? 'text-right' : 'text-left'}`}
                                >
                                    {c.label}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((r, i) => (
                            <tr key={i} className="border-t border-ark-line/50 hover:bg-ark-tag/50">
                                {columns.map((c) => (
                                    <td
                                        key={c.key}
                                        className={`p-2 ${c.numeric ? 'text-right font-mono text-ark-fg' : 'text-ark-fg-dim'}`}
                                    >
                                        {fmt(r[c.key], c.numeric)}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
