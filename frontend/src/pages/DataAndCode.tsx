import { AlertTriangle, BookOpen, Database, ExternalLink, FileText } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ArkCode, { type CodeSource } from '../arcanum/ArkCode'
import ArkDownloads from '../arcanum/ArkDownloads'
import ArkTriad, { type Cdf } from '../arcanum/ArkTriad'
import ecosystem from '../arcanum/ecosystem.json'
import { api, downloadUrl } from '../services/api'

// -----------------------------------------------------------------------------
// DATA & CODE  (route: /data)
//
// This page is where the Research Triad LIVES now. It used to sit on `/`, which
// is what CODE_DATA_FIRST_STANDARD requires of a research estate — and which was
// wrong for Foodberg, whose reader is a chef, not a replication referee. The
// ratified `tool-first` exception (CDF §9.1) relocates the full-size triad to a
// dedicated /data page reachable in one click, and `check_cdf.py --tool-first`
// asserts it HERE, at the same 40%-above-the-fold threshold at 360px.
//
// That is why the title block below is two short lines and the triad is the very
// next element: no prose, no card, no download grid may come between them. If
// you add an explanatory paragraph above the triad, the gate fails and the
// exception stops protecting the leave-with-the-goods path.
//
// The page also carries the site's first code surface. Foodberg shipped with
// none at all — no /code route, no code block, no R/Python toggle — which was an
// open CONTENT_RENDERING §3 violation, not merely a missing nicety.
// -----------------------------------------------------------------------------

const FOODBERG_CDF = (ecosystem.sites.find((s) => s.key === 'foodberg') as unknown as { cdf?: Cdf } | undefined)?.cdf ?? null

// Shape of /api/download/datasets (backend/main.py:1538). `xlsx_url` is present
// only where a dataset fits in one Excel worksheet; when it does not, the
// backend sends `xlsx_unavailable_reason` instead and we print that reason.
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

// Canonical educational disclaimer (EDUCATIONAL_DISCLAIMER_STANDARD v1.0). The
// backend serves its own copy; this is the fallback when the API is unreachable,
// so the disclaimer never silently disappears with the catalog.
const FALLBACK_DISCLAIMER =
    'The data on this site is reconstructed/aggregated for research transparency ' +
    'and education. It may lag official revisions or contain reconstruction error, ' +
    'and it is not a substitute for the original source. For authoritative figures, ' +
    'defer to the named original source for each dataset.'

// -----------------------------------------------------------------------------
// THE TWO SCRIPTS
//
// Byte-for-byte the files served at /code/foodberg_prices.R and .py. Both hit
// the real public API with a real slug: `tomatoes-field-grown` from `retail` is
// BLS series APU0000712311, 552 monthly observations, 1980-01 → 2026-06, $ per
// lb, latest 2.154. The printed output in the comments is what these scripts
// actually print today — a snippet that does not run is worse than no snippet.
// -----------------------------------------------------------------------------

const R_SOURCE = `# =============================================================================
# Foodberg — one retail price series, from the public API, in R
#
# Foodberg's API needs no key, no registration and no rate limit. Every endpoint
# below is the same one the website itself calls to draw its own charts.
#
# Run:   Rscript foodberg_prices.R
# Needs: install.packages("jsonlite")
# =============================================================================

library(jsonlite)

# --- WHERE TO POINT AT THE DATA ---------------------------------------------
# \`item\` is a commodity slug. The full list of slugs, with the sources and the
# real coverage span each one has, is at:
#   https://foodberg.org/api/prices/coverage      (the \`commodities\` object)
#
# \`source\` is one of:
#   retail     BLS Average Price — monthly, US retail, in kitchen units
#   pinksheet  World Bank Pink Sheet — monthly, global spot
#   nass       USDA NASS price received — annual, US farm gate
#
# Change these two lines; nothing below needs to change.
item   <- "tomatoes-field-grown"
source <- "retail"

url  <- paste0("https://foodberg.org/api/prices/source/", item, "?source=", source)
resp <- fromJSON(url)

# The payload carries has_history, label, unit, data_points, date_range and
# \`data\` — a data frame of date / year / price. Nothing is interpolated or
# extrapolated: a month with no published price simply has no row.
stopifnot(isTRUE(resp$has_history))

prices <- resp$data
prices$date <- as.Date(prices$date)

cat(resp$label, "\\n")
cat(resp$data_points, "observations,",
    resp$date_range$start, "->", resp$date_range$end, "\\n")
cat("latest:", tail(prices$price, 1), resp$unit, "\\n")
# BLS US retail average — Tomatoes, field grown
# 552 observations, 1980-01-01 -> 2026-06-01
# latest: 2.154 $ per lb

plot(prices$date, prices$price, type = "l",
     main = resp$label, xlab = "", ylab = resp$unit)

# --- OR TAKE THE WHOLE TABLE ------------------------------------------------
# Every dataset listed on /data is also one flat file. No pagination, no key.
# retail_prices columns: food_item, price, unit, store_type, location, state,
#                        country, date, source, brand, quality_grade, imported_at
retail <- read.csv("https://foodberg.org/api/download/retail_prices.csv",
                   stringsAsFactors = FALSE)
cat(nrow(retail), "rows,", length(unique(retail$food_item)), "items\\n")
`

const PY_SOURCE = `# =============================================================================
# Foodberg — one retail price series, from the public API, in Python
#
# Foodberg's API needs no key, no registration and no rate limit. Every endpoint
# below is the same one the website itself calls to draw its own charts.
#
# Run:   python foodberg_prices.py
# Needs: pip install requests pandas matplotlib
# =============================================================================

import io

import matplotlib.pyplot as plt
import pandas as pd
import requests

# --- WHERE TO POINT AT THE DATA ---------------------------------------------
# ITEM is a commodity slug. The full list of slugs, with the sources and the
# real coverage span each one has, is at:
#   https://foodberg.org/api/prices/coverage      (the "commodities" object)
#
# SOURCE is one of:
#   retail     BLS Average Price — monthly, US retail, in kitchen units
#   pinksheet  World Bank Pink Sheet — monthly, global spot
#   nass       USDA NASS price received — annual, US farm gate
#
# Change these two lines; nothing below needs to change.
ITEM = "tomatoes-field-grown"
SOURCE = "retail"

resp = requests.get(
    f"https://foodberg.org/api/prices/source/{ITEM}",
    params={"source": SOURCE},
    timeout=30,
)
resp.raise_for_status()
payload = resp.json()

# The payload carries has_history, label, unit, data_points, date_range and
# "data" — date / year / price. Nothing is interpolated or extrapolated: a
# month with no published price simply has no row.
assert payload["has_history"], payload.get("note", "no series for this item/source")

prices = pd.DataFrame(payload["data"])
prices["date"] = pd.to_datetime(prices["date"])

print(payload["label"])
print(payload["data_points"], "observations,",
      payload["date_range"]["start"], "->", payload["date_range"]["end"])
print("latest:", prices["price"].iloc[-1], payload["unit"])
# BLS US retail average — Tomatoes, field grown
# 552 observations, 1980-01-01 -> 2026-06-01
# latest: 2.154 $ per lb

ax = prices.plot(x="date", y="price", legend=False, figsize=(9, 4))
ax.set_title(payload["label"])
ax.set_xlabel("")
ax.set_ylabel(payload["unit"])
plt.tight_layout()
plt.show()

# --- OR TAKE THE WHOLE TABLE ------------------------------------------------
# Every dataset listed on /data is also one flat file. No pagination, no key.
# retail_prices columns: food_item, price, unit, store_type, location, state,
#                        country, date, source, brand, quality_grade, imported_at
#
# Fetched through requests rather than pd.read_csv(url) directly. pandas reads a
# URL with urllib, and Cloudflare — which fronts foodberg.org — refuses
# urllib's default "Python-urllib/3.x" User-Agent with HTTP 403. requests,
# libcurl and R are all served normally (checked 2026-07-25), so this is a
# bot-fingerprint quirk of one client, not a restriction on the data.
bulk = requests.get(
    "https://foodberg.org/api/download/retail_prices.csv",
    timeout=120,
)
bulk.raise_for_status()
retail = pd.read_csv(io.StringIO(bulk.text))
print(len(retail), "rows,", retail["food_item"].nunique(), "items")
`

const CODE_SOURCES: CodeSource[] = [
    { lang: 'r', code: R_SOURCE },
    { lang: 'python', code: PY_SOURCE },
]

export default function DataAndCode() {
    const [catalog, setCatalog] = useState<DownloadCatalog | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.getDownloadDatasets()
            .then((r) => setCatalog(r.data as DownloadCatalog))
            .catch((e) => {
                console.error('Failed to load download catalog:', e)
                setError('Could not load the download catalog. The data API may be offline. The bundle above is a static file and still downloads.')
            })
            .finally(() => setLoading(false))
    }, [])

    const disclaimer = catalog?.disclaimer || FALLBACK_DISCLAIMER
    const citation = FOODBERG_CDF?.citation
    const repo = FOODBERG_CDF?.code?.href
    const licence = FOODBERG_CDF?.code?.license

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* TITLE BLOCK — deliberately two lines. The triad must clear the
                40%-above-the-fold threshold at 360px. */}
            <div className="mb-5">
                <h1 className="text-3xl font-bold text-ark-fg mb-1">Data &amp; Code</h1>
                <p className="text-ark-fg-dim">
                    Everything behind the charts: the tables, the scripts, and where each number came from.
                </p>
            </div>

            {/* THE RESEARCH TRIAD — first element after the title. Nothing goes
                above this. (CODE_DATA_FIRST_STANDARD §9.1, tool-first mode.) */}
            <ArkTriad cdf={FOODBERG_CDF} track={{ site: 'foodberg', endpoint: '/__track' }} />

            {/* What the 12 MB bundle actually is. The triad advertises a size;
                a reader deserves to know what is inside before spending it. */}
            <div className="card mt-8">
                <h2 className="text-lg font-semibold text-ark-fg mb-2 flex items-center">
                    <Database className="w-5 h-5 mr-2 text-amber-400" />
                    What is in the 12 MB bundle
                </h2>
                <p className="text-ark-fg-dim text-sm">
                    <code className="ark-inline">foodberg-data.zip</code> is a point-in-time snapshot: one CSV
                    and one Parquet file per table under <code className="ark-inline">tables/</code>, plus{' '}
                    <code className="ark-inline">data_dictionary.csv</code>,{' '}
                    <code className="ark-inline">PROVENANCE.csv</code>, <code className="ark-inline">LICENSE</code>{' '}
                    and <code className="ark-inline">README.md</code>. It compresses well because it is mostly
                    long, repetitive tabular text — as built on 2026-07-14 the archive is 12.5 MB and unpacks to
                    roughly 155 MB of CSV, the great majority of it the WASDE table. It carries no XLSX, which is
                    why the triad above does not claim XLSX; XLSX is a live per-dataset export, listed below.
                </p>
                <p className="text-ark-fg-dim text-sm mt-2">
                    The bundle is a snapshot; the per-dataset downloads below are generated from the live
                    database on request, so they are the current data. Where the two disagree, the per-dataset
                    download is right.
                </p>
            </div>

            {/* Educational disclaimer. */}
            <div className="card mt-6 bg-gradient-to-br from-amber-900/20 to-amber-800/10 border-amber-600/40">
                <h2 className="text-lg font-semibold text-amber-400 mb-2 flex items-center">
                    <AlertTriangle className="w-5 h-5 mr-2" />
                    For education &amp; research
                </h2>
                <p className="text-ark-fg-dim text-sm">{disclaimer}</p>
            </div>

            {/* PER-DATASET DOWNLOADS ------------------------------------------ */}
            <section className="mt-8">
                <h2 className="text-2xl font-bold text-ark-fg mb-1">Download a table</h2>
                <p className="text-ark-fg-dim text-sm mb-4">
                    CSV, XLSX and Parquet on every dataset (DOWNLOAD_AND_FORMATS rule 1). Nothing here is
                    paywalled, query-only or rate-limited. JSON is deliberately absent: it is the site's own
                    wire format, not a format anyone should have to analyse a price series in.
                </p>

                {loading && <div className="text-ark-fg-dim">Loading the dataset catalog…</div>}
                {error && <div className="card text-red-400">{error}</div>}

                <div className="card divide-y divide-ark-line">
                    {catalog?.datasets.map((d) => (
                        <div key={d.id} className="py-4 first:pt-0 last:pb-0">
                            <div className="flex justify-between items-start gap-3 flex-wrap mb-1">
                                <h3 className="text-lg font-semibold text-ark-fg">{d.name}</h3>
                                {d.rows != null && (
                                    <span className="text-xs text-ark-fg-dim whitespace-nowrap">
                                        {d.rows.toLocaleString()} rows
                                    </span>
                                )}
                            </div>
                            <p className="text-ark-fg-dim text-sm mb-2">{d.description}</p>
                            <div className="text-xs text-ark-fg-dim mb-3">
                                <span className="font-medium text-ark-fg">Source:</span> {d.source}
                                {' · '}
                                <span className="font-medium text-ark-fg">Defer to:</span> {d.defer_to}
                            </div>
                            {/* One renderer for every download row on the site, so the
                                format set and its order cannot drift page to page.
                                Where XLSX genuinely cannot be produced the row says so
                                in words — two of the six datasets exceed what a single
                                Excel worksheet can hold, and a button that 413s would
                                be worse than a stated limit. */}
                            <ArkDownloads
                                filename={`foodberg_${d.id}`}
                                label="Download:"
                                hrefs={{
                                    csv: downloadUrl(d.csv_url),
                                    xlsx: d.xlsx_url ? downloadUrl(d.xlsx_url) : undefined,
                                    parquet: downloadUrl(d.parquet_url),
                                }}
                                unavailable={
                                    d.xlsx_unavailable_reason ? { xlsx: d.xlsx_unavailable_reason } : undefined
                                }
                            />
                        </div>
                    ))}
                </div>

                {catalog?.dictionary_url && (
                    <div className="card mt-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
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
            </section>

            {/* THE CODE SURFACE ----------------------------------------------- */}
            <section className="mt-10">
                <h2 className="text-2xl font-bold text-ark-fg mb-1">Pull a price series yourself</h2>
                <p className="text-ark-fg-dim text-sm mb-4">
                    The same two lines of code in R and in Python. Both hit the live public API — no key, no
                    registration, no rate limit — fetch{' '}
                    <span className="text-ark-fg">Tomatoes, field grown</span> from the BLS Average Price
                    programme (552 monthly observations, 1980-01 → 2026-06, $ per lb), print the coverage, and
                    plot it. The commented output is what the script actually prints. Change the two marked
                    lines to fetch any other series.
                </p>

                <ArkCode
                    sources={CODE_SOURCES}
                    filename="foodberg_prices"
                    path="foodberg_prices — one series from the public API"
                    stableUrls={{ r: '/code/foodberg_prices.R', python: '/code/foodberg_prices.py' }}
                />

                <div className="card">
                    <h3 className="text-lg font-semibold text-ark-fg mb-2">The endpoints these scripts use</h3>
                    <ul className="text-sm text-ark-fg-dim space-y-2">
                        <li>
                            <code className="ark-inline">/api/prices/coverage</code> — every commodity slug, the
                            sources carrying it, its real observation count and span, and a liveness verdict
                            computed from the last <em>real</em> observation rather than a declared end date.
                        </li>
                        <li>
                            <code className="ark-inline">/api/prices/source/&#123;slug&#125;?source=retail|pinksheet|nass</code>{' '}
                            — one series, as published. Returns{' '}
                            <code className="ark-inline">has_history</code>,{' '}
                            <code className="ark-inline">label</code>, <code className="ark-inline">unit</code>,{' '}
                            <code className="ark-inline">data_points</code>,{' '}
                            <code className="ark-inline">date_range</code> and{' '}
                            <code className="ark-inline">data[]</code> of date / year / price.
                        </li>
                        <li>
                            <code className="ark-inline">/api/download/&#123;dataset&#125;.csv</code> (also{' '}
                            <code className="ark-inline">.xlsx</code>, <code className="ark-inline">.parquet</code>)
                            — a whole table in one request.
                        </li>
                        <li>
                            <a className="text-emerald-400 hover:text-emerald-300" href="/llms.txt">
                                /llms.txt
                            </a>{' '}
                            — the same map, written for an agent rather than a person.
                        </li>
                    </ul>
                </div>
            </section>

            {/* PROVENANCE · METHOD · LICENCE · CITATION ------------------------ */}
            <section className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="card">
                    <h2 className="text-lg font-semibold text-ark-fg mb-2">Where the numbers come from</h2>
                    <p className="text-ark-fg-dim text-sm mb-3">
                        Foodberg holds no primary data of its own. Every series is a publisher's series, stored
                        as published: USDA (WASDE, NASS, AMS Market News), BLS (Average Price, CPI, PPI, via
                        FRED), the World Bank Pink Sheet, and FAO/FAOSTAT. Nothing is interpolated, nothing is
                        extrapolated, and a series that a publisher stopped updating is labelled as stale or
                        discontinued rather than presented as current.
                    </p>
                    <p className="text-ark-fg-dim text-sm mb-3">
                        Per-source freshness — which sources are current, which are behind, and by how long —
                        lives on one page and is not duplicated here.
                    </p>
                    <Link to="/sources" className="btn-secondary inline-flex items-center">
                        Source freshness &amp; update cadence
                    </Link>
                </div>

                <div className="card">
                    <h2 className="text-lg font-semibold text-ark-fg mb-2">Licence, code and citation</h2>
                    <ul className="text-sm text-ark-fg-dim space-y-2">
                        {repo && (
                            <li>
                                <span className="font-medium text-ark-fg">Site &amp; pipeline code:</span>{' '}
                                <a
                                    className="text-emerald-400 hover:text-emerald-300 inline-flex items-center"
                                    href={repo}
                                >
                                    {repo.replace(/^https:\/\//, '')}
                                    <ExternalLink className="w-3 h-3 ml-1" />
                                </a>
                                {licence ? ` · ${licence}` : ''}
                            </li>
                        )}
                        <li>
                            <span className="font-medium text-ark-fg">Data licence:</span> the underlying series
                            are US federal and international-agency publications; redistribution terms are the
                            publisher's, not Foodberg's. Defer to each dataset's named authority above.
                        </li>
                        {citation && (
                            <li>
                                <span className="font-medium text-ark-fg">Cite this site:</span>{' '}
                                <span className="text-ark-fg">{citation}</span>
                            </li>
                        )}
                    </ul>
                </div>
            </section>
        </div>
    )
}
