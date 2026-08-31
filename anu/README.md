# Foodberg — Anu Replication Package

Self-contained replication pipeline for the Foodberg dataset: global and U.S. food
and commodity prices from public sources (World Bank, FAO, USDA, BLS, FRED).

**Anyone with public internet access and Python 3.10+ can reproduce every data
series this site serves.** No private data, no internal paths, no API keys
required except the optional USDA NASS step (free instant registration).

## What it produces

| Family | Series | Source | Access |
|---|---|---|---|
| World Bank Pink Sheet (`ps_*`) | 71 monthly commodity prices (wheat, maize, rice, coffee, beef, sugar, oils, …) | World Bank | keyless |
| FAO Food Price Index (`fao_fpi_*`) | 6 monthly indices (headline + meat/dairy/cereals/oils/sugar) | FAO | keyless |
| FRED indicators (`CPI*`, `WPU*`, `GDPDEF`, …) | 14 monthly/quarterly macro & food-price series | FRED | keyless |
| BLS CPI (NSA) (`CUUR*`) | 9 monthly food CPI series | BLS public API | keyless |
| BLS Average Prices (`APU*`) | 51 monthly U.S. retail food prices | BLS via FRED | keyless |
| FAOSTAT producer prices (`faostat_producer_prices`) | family: annual USD/tonne per country × item | FAOSTAT | keyless (large) |
| FAOSTAT food CPI (`faostat_food_cpi`) | family: monthly food CPI per country | FAOSTAT | keyless (large) |
| Foodberg composites (`foodberg_global_composite`, `bls_overall`) | 2 derived indices | this package | derived |
| USDA NASS WASDE (`usda_nass_wasde`) | family: price received / production / yield, 48 commodities | USDA NASS | free key (optional) |

**156 registry entries** in total — see `series_registry.json` (the canonical data
contract: every series' source, license, units, frequency, coverage, construction).

## Quick start

```bash
cd anu/
pip install -r requirements.txt
make all        # full pipeline: ~6 fetchers -> 6 processors -> validator
                # (downloads two FAOSTAT bulk zips, ~400 MB expanded)
make quick      # everything except FAOSTAT + NASS; validator tolerates the gaps
make nass       # optional USDA family: NASS_API_KEY=<key> required
```

Or script-by-script (`python scripts/L01_fetch_pinksheet.py`, …) — see
`scripts/README.md` for the full order and per-script notes.

## Layout

```
anu/
  series_registry.json   canonical registry (156 entries)
  scripts/               L## fetchers, P## processors, V01 validator
  dpr/                   D01–D07 data provenance records
  data/                  produced at run time (gitignored)
    raw/                 source downloads, each with a .fetch_meta.json sidecar
    processed/           reserved for intermediate stages
    final/               validated output — one CSV per series (plus family CSVs)
  requirements.txt       requests, openpyxl
  Makefile               make all | quick | nass | clean
```

## Data ethics

- **Verbatim values only.** Every number in `data/final/` is a publisher's own
  observation or an explicitly documented derived computation (the two composites).
  Missing values are dropped, never imputed.
- **Recompute-vs-publish rule.** Series carrying a publisher's name (e.g.
  `fao_fpi_overall`) carry that publisher's published numbers, never a recomputation.
  Foodberg's own constructions live under Foodberg names (`foodberg_global_composite`,
  `bls_overall`).
- **Provenance per artifact.** Every raw download has a `.fetch_meta.json` sidecar
  recording its URL and fetch context.
- **No synthetic data, ever.**

## Licenses

Package code: MIT (same as the repository). Data: each source's own license is
recorded per series in `series_registry.json` (CC BY 4.0 for World Bank/FAO/FAOSTAT;
public domain for U.S. federal sources).
