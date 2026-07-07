/* ReindexControl + reindex transform — Carson Universal Graph Contract.

   Client-side reindexing for index/comparable charts: pick a base year and every
   displayed series is rescaled so it equals 100 at that year
   (value_t / value_baseYear * 100). Everything is recomputed in-browser from the
   already-loaded rows — no server round-trip. Series with no value at the chosen
   base year are skipped gracefully (left as-is / dropped from that row's rescale)
   so we never fabricate a base point. */

interface ReindexControlProps {
    /** Distinct base-year options, ascending. */
    years: number[]
    /** Currently selected base year, or null = "off" (raw values). */
    baseYear: number | null
    onChange: (year: number | null) => void
    /** id stem to keep the label/select association unique per chart. */
    id?: string
}

/** Small dropdown placed to the LEFT of the Download CSV control. */
export function ReindexControl({ years, baseYear, onChange, id = 'reindex' }: ReindexControlProps) {
    if (!years.length) return null
    return (
        <div className="flex items-center gap-2">
            <label htmlFor={id} className="text-xs text-ark-fg-dim whitespace-nowrap">
                Reindex base
            </label>
            <select
                id={id}
                value={baseYear ?? ''}
                onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
                className="px-2 py-1.5 bg-ark-tag border border-ark-line rounded-lg text-sm text-ark-fg focus:outline-none focus:border-emerald-500"
                title="Rescale every series to 100 at the chosen base year (computed in-browser)"
            >
                <option value="">Off (raw)</option>
                {years.map((y) => (
                    <option key={y} value={y}>{y} = 100</option>
                ))}
            </select>
        </div>
    )
}

/**
 * Reindex an array of chart rows. Each row is keyed by a year field plus one or
 * more numeric series keys. For every series key, the value at `baseYear` is the
 * divisor; the series is rescaled to (value / base) * 100. A series lacking a
 * finite value at `baseYear` is left untouched (skipped) so we never invent a
 * base point.
 *
 * @param rows      already-loaded chart rows (NOT mutated)
 * @param seriesKeys numeric keys to rescale (e.g. ['wheat','corn'] or ['fao_overall'])
 * @param baseYear  chosen base year; null returns rows unchanged
 * @param yearKey   the field holding the year (default 'year')
 */
export function reindexRows<T extends Record<string, unknown>>(
    rows: T[],
    seriesKeys: string[],
    baseYear: number | null,
    yearKey = 'year',
): T[] {
    if (baseYear == null || !rows.length) return rows

    // Find the base value for each series at the chosen base year.
    const baseRow = rows.find((r) => Number(r[yearKey]) === baseYear)
    const baseVals: Record<string, number> = {}
    for (const key of seriesKeys) {
        const v = baseRow ? baseRow[key] : undefined
        if (typeof v === 'number' && isFinite(v) && v !== 0) baseVals[key] = v
    }

    return rows.map((r) => {
        const out: Record<string, unknown> = { ...r }
        for (const key of seriesKeys) {
            const base = baseVals[key]
            const v = r[key]
            // Only rescale when both this row's value and the base are finite.
            if (base !== undefined && typeof v === 'number' && isFinite(v)) {
                out[key] = (v / base) * 100
            }
            // else: leave the original value (series has no base → skip gracefully)
        }
        return out as T
    })
}

/** Distinct, ascending list of years present in `rows` under `yearKey`. */
export function distinctYears(rows: Array<Record<string, unknown>>, yearKey = 'year'): number[] {
    const set = new Set<number>()
    for (const r of rows) {
        const y = Number(r[yearKey])
        if (isFinite(y)) set.add(y)
    }
    return Array.from(set).sort((a, b) => a - b)
}

/* ----- date-keyed variant (rows keyed by a 'YYYY-MM' / 'YYYY-...' date) ----- */

/** Distinct, ascending list of years parsed from a date field (e.g. 'YYYY-MM'). */
export function distinctYearsFromDate(
    rows: Array<Record<string, unknown>>,
    dateKey = 'date',
): number[] {
    const set = new Set<number>()
    for (const r of rows) {
        const y = Number(String(r[dateKey] ?? '').slice(0, 4))
        if (isFinite(y) && y > 0) set.add(y)
    }
    return Array.from(set).sort((a, b) => a - b)
}

/**
 * Reindex rows keyed by a date string (e.g. monthly 'YYYY-MM'). For each series
 * the base divisor is that series' FIRST finite observation within `baseYear`
 * (earliest month present), giving baseYear ≈ 100. Series with no finite value
 * anywhere in the base year are skipped (left as raw) — never fabricated.
 */
export function reindexRowsByDate<T extends Record<string, unknown>>(
    rows: T[],
    seriesKeys: string[],
    baseYear: number | null,
    dateKey = 'date',
): T[] {
    if (baseYear == null || !rows.length) return rows

    const prefix = String(baseYear)
    const baseVals: Record<string, number> = {}
    for (const key of seriesKeys) {
        // earliest in-baseYear row that has a finite value for this series
        for (const r of rows) {
            if (String(r[dateKey] ?? '').slice(0, 4) !== prefix) continue
            const v = r[key]
            if (typeof v === 'number' && isFinite(v) && v !== 0) { baseVals[key] = v; break }
        }
    }

    return rows.map((r) => {
        const out: Record<string, unknown> = { ...r }
        for (const key of seriesKeys) {
            const base = baseVals[key]
            const v = r[key]
            if (base !== undefined && typeof v === 'number' && isFinite(v)) {
                out[key] = (v / base) * 100
            }
        }
        return out as T
    })
}
