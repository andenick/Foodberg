import { AlertTriangle, BookOpen, Database, Download, FileText } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, downloadUrl } from '../services/api'

interface DownloadDataset {
    id: string
    name: string
    description: string
    source: string
    defer_to: string
    formats: string[]
    csv_url: string
    xlsx_url?: string
    xlsx_unavailable_reason?: string
    parquet_url: string
    rows: number | null
}

interface DownloadCatalog {
    datasets: DownloadDataset[]
    dictionary_url: string
    disclaimer: string
}

// Canonical educational disclaimer (EDUCATIONAL_DISCLAIMER_STANDARD v1.0).
const FALLBACK_DISCLAIMER =
    'The data on this site is reconstructed/aggregated for research transparency ' +
    'and education. It may lag official revisions or contain reconstruction error, ' +
    'and it is not a substitute for the original source. For authoritative figures, ' +
    'defer to the named original source for each dataset.'

export default function Downloads() {
    const [catalog, setCatalog] = useState<DownloadCatalog | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api
            .getDownloadDatasets()
            .then((r) => setCatalog(r.data))
            .catch((e) => {
                console.error('Failed to load download catalog:', e)
                setError('Could not load the download catalog. The data API may be offline.')
            })
            .finally(() => setLoading(false))
    }, [])

    const disclaimer = catalog?.disclaimer || FALLBACK_DISCLAIMER

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-ark-fg mb-2 flex items-center">
                    <Download className="w-8 h-8 mr-3 text-amber-400" />
                    Data &amp; Downloads
                </h1>
                <p className="text-ark-fg-dim">
                    Download the underlying datasets that power Foodberg — each as a full CSV or
                    Parquet file — plus a data dictionary describing every column. Nothing here is
                    paywalled or query-only: the data is yours to take.
                </p>
            </div>

            {/* Educational disclaimer */}
            <div className="card mb-8 bg-gradient-to-br from-amber-900/20 to-amber-800/10 border-amber-700/30">
                <h2 className="text-lg font-semibold text-amber-400 mb-2 flex items-center">
                    <AlertTriangle className="w-5 h-5 mr-2" />
                    For education &amp; research
                </h2>
                <p className="text-ark-fg-dim text-sm">{disclaimer}</p>
            </div>

            {/* Data dictionary */}
            {catalog?.dictionary_url && (
                <div className="card mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div className="flex items-start">
                        <BookOpen className="w-6 h-6 mr-3 text-emerald-400 shrink-0" />
                        <div>
                            <h3 className="text-lg font-semibold text-ark-fg">Data dictionary</h3>
                            <p className="text-ark-fg-dim text-sm">
                                One CSV documenting every column of every dataset, with its upstream
                                authority. Read this first.
                            </p>
                        </div>
                    </div>
                    <a
                        href={downloadUrl(catalog.dictionary_url)}
                        className="btn-primary inline-flex items-center whitespace-nowrap"
                    >
                        <FileText className="w-4 h-4 mr-2" />
                        dictionary.csv
                    </a>
                </div>
            )}

            {loading && <div className="text-ark-fg-dim">Loading datasets…</div>}
            {error && <div className="card text-red-400">{error}</div>}

            {/* Dataset cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {catalog?.datasets.map((d) => (
                    <div key={d.id} className="card flex flex-col">
                        <div className="flex justify-between items-start mb-3">
                            <h3 className="text-xl font-semibold text-ark-fg flex items-center">
                                <Database className="w-5 h-5 mr-2 text-amber-400" />
                                {d.name}
                            </h3>
                            {d.rows != null && (
                                <span className="text-xs text-ark-fg-dim whitespace-nowrap">
                                    {d.rows.toLocaleString()} rows
                                </span>
                            )}
                        </div>

                        <p className="text-ark-fg-dim text-sm mb-4 grow">{d.description}</p>

                        <div className="text-xs text-ark-fg-dim mb-4">
                            <div>
                                <span className="font-medium text-ark-fg">Source:</span> {d.source}
                            </div>
                            <div>
                                <span className="font-medium text-ark-fg">Defer to:</span>{' '}
                                {d.defer_to}
                            </div>
                        </div>

                        {/* CSV / XLSX / Parquet — the three formats
                            DOWNLOAD_AND_FORMATS_STANDARD rule 1 requires. XLSX
                            was missing until 2026-07-24. */}
                        <div className="flex gap-3 pt-4 border-t border-ark-line flex-wrap">
                            <a
                                href={downloadUrl(d.csv_url)}
                                className="btn-primary inline-flex items-center"
                            >
                                <Download className="w-4 h-4 mr-2" />
                                CSV
                            </a>
                            {/* XLSX is offered only where the dataset fits in one
                                Excel worksheet; the backend omits xlsx_url and
                                explains why when it does not. */}
                            {d.xlsx_url ? (
                                <a
                                    href={downloadUrl(d.xlsx_url)}
                                    className="btn-secondary inline-flex items-center"
                                >
                                    <Download className="w-4 h-4 mr-2" />
                                    XLSX
                                </a>
                            ) : d.xlsx_unavailable_reason ? (
                                <span
                                    title={d.xlsx_unavailable_reason}
                                    className="inline-flex items-center text-xs text-ark-fg-dim px-2"
                                >
                                    XLSX unavailable — too many rows for Excel
                                </span>
                            ) : null}
                            <a
                                href={downloadUrl(d.parquet_url)}
                                className="btn-secondary inline-flex items-center"
                            >
                                <Download className="w-4 h-4 mr-2" />
                                Parquet
                            </a>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
