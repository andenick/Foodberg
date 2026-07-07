# Carson Site Note — Foodberg build-out backlog (2026-06-19)

Captured from the user's website walkthrough during the Carson "site sharpening" initiative.
A **note, not a build order** — the pipeline/data work below is deferred; only the site-level DNA
fixes are near-term.

## Site status (foodberg.org, React)
Front page is good (quotes, Food Price Index, long history). Near-term site fixes (tracked as Carson
`P5-foodberg`): add a **reindex control** (reindex indices to a common base year — button left of the
Download CSV; optionally normalize to US CPI), ensure every graph has the **top-right Download CSV**
(Historical Trends / commodities are missing it), and **drop any series with only one year of data**
from the Price Explorer.

## Deferred project build-out (the real data work, later)
- **Longer-term food index pre-2015** — construct an own food CPI / price index reaching before 2015,
  from historical sources (or build our own index). The current series start too late.
- **Full WASDE history** — the Price Explorer currently exposes WASDE with only a single marketing year
  (2025). Pull the **complete WASDE back-history** if available; a one-year series is inadequate for an
  Explorer (and violates the "no single-year series in an Explorer" data rule).
- **More regions + more comparison methods + per-food comparisons** — the geographic comparison is good
  (regions added, livestock production index is strong); expand regions, add comparison methods, and
  per-food comparisons.

## Data honesty rules to respect
- No single-year series surfaced in the Explorer (carson-data lens).
- No fabricated/placeholder values — if pre-2015 data can't be sourced, mark unavailable, don't invent.
- Downloads CSV + Parquet only (no JSON).

Related: master walkthrough plan Part C2 + Part D; Carson standards under
`Council/Carson/Technical/standards/`.
