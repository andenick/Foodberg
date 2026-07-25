import ArkDownloads from '../arcanum/ArkDownloads'

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

/**
 * The site's one data table.
 *
 * TABLE_RENDERING_STANDARD rules 1 & 3: this used to be a bare
 * `overflow-x-auto` div — a wide table became a horizontally-scrolling mystery
 * on a phone, with no way to tell which column a number belonged to. It now
 * emits the kit's `.ark-table-wrap` / `.ark-table` markup and stamps every cell
 * with `data-label`, which is what the vendored arcanum.css §18 reflow reads to
 * turn each row into a label-stacked card below 680px. Upgrading this component
 * fixes every table on the site at once, which is the point of a shared kit.
 *
 * Downloads go through <ArkDownloads/> so every table offers the same formats
 * in the same order as every chart (DOWNLOAD_AND_FORMATS_STANDARD rule 2).
 */
export function ScrollableDataTable({
    rows,
    columns,
    filename,
    maxHeight = 320,
    downloads,
    downloadsUnavailable,
    title,
}: {
    rows: Array<Record<string, unknown>>
    columns: Array<{ key: string; label: string; numeric?: boolean }>
    filename: string
    maxHeight?: number
    /** Server-side bulk formats where this table has them (XLSX/Parquet). */
    downloads?: { xlsx?: string; parquet?: string }
    downloadsUnavailable?: { xlsx?: string; parquet?: string }
    title?: string
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
            <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                <h3 className="text-sm font-semibold text-ark-fg-dim uppercase tracking-wide">
                    {title ?? 'Plotted data'} ({rows.length.toLocaleString()} rows)
                </h3>
                <ArkDownloads
                    rows={rows}
                    filename={filename}
                    hrefs={downloads}
                    unavailable={downloadsUnavailable}
                    label={null}
                />
            </div>
            <div
                className="ark-table-wrap overflow-y-auto"
                style={{ maxHeight }}
                role="region"
                tabIndex={0}
                aria-label={title ?? 'Plotted data'}
            >
                <table className="ark-table">
                    <thead>
                        <tr>
                            {columns.map((c) => (
                                <th
                                    key={c.key}
                                    scope="col"
                                    className={c.numeric ? 'text-right' : 'text-left'}
                                >
                                    {c.label}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((r, i) => (
                            <tr key={i}>
                                {columns.map((c) => (
                                    <td
                                        key={c.key}
                                        /* Read by the §18 reflow to show the column
                                           header beside the value on narrow screens. */
                                        data-label={c.label}
                                        className={c.numeric ? 'text-right font-mono text-ark-fg' : 'text-ark-fg-dim'}
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
