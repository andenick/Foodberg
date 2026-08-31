# D07: Foodberg composite indices — Data Provenance Record

## What this covers
The two derived composite indices the site computes itself (as opposed to passing a
publisher's series through):
- `foodberg_global_composite` — fixed-weight average of the five FAO sub-indices.
- `bls_overall` — fixed-weight average of five BLS CPI-U (NSA) food components.

## Source
Derived series; inputs are the outputs of D03 (FAO FPI) and D04 (BLS CUUR).

## Construction method
`P06_construct_composites.py` mirrors the deployed site's computation exactly:

**foodberg_global_composite** (monthly):
weights meat 0.348, cereals 0.272, dairy 0.173, oils 0.135, sugar 0.072 (FAO's published
average trade-share weights). For every month with **≥ 4 of 5** components present, the
composite is Σ(wᵢ·vᵢ)/Σ(wᵢ) over present components (weights renormalized), rounded to
2 decimals.

**bls_overall** (monthly):
weights CUUR0000SAF112 (meats/poultry/fish/eggs) 0.30, CUUR0000SAF111 (cereals/bakery)
0.20, CUUR0000SAF113 (fruits/vegetables) 0.18, CUUR0000SEFV (food away from home) 0.17,
CUUR0000SEFJ (dairy) 0.15 — approximate US consumer expenditure shares. For every month
with **≥ 3 of 5** components present, same renormalized weighted average, 2 decimals.

## Transformations applied
Weighted averaging only. No rebasing, no deflation, no interpolation of absent months.

## Known issues
- **Naming rule (critical):** these are Foodberg constructions. `foodberg_global_composite`
  is NOT the FAO Food Price Index (FAO chains with trade-share weights that vary by
  year; a fixed-weight average diverges by up to ~4 index points) and must never be
  labelled with FAO's name — `fao_fpi_overall` is FAO's own published number.
  `bls_overall` is not a BLS publication; BLS publishes no overall food index under
  this definition.
- Base periods: 2014–2016 = 100 (global composite, inherited from FAO inputs);
  1982–84 = 100 (US composite, inherited from CPI inputs).

## Validation
V01 checks both series: presence, positive values, coverage containing 1990-01 → current
(global) and the declared start → current (US) with 2-month slack. The `n_components`
column lets users audit which months are renormalized over fewer than 5 components.
