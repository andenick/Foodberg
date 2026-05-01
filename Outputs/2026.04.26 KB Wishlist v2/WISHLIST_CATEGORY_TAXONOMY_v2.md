# Foodberg KB Wishlist v2 — Category Taxonomy

**Version**: 2.0
**Date**: 2026-04-26
**Total categories**: 25 (14 inherited from v1 + 11 new)

---

## Schema v2.0 — Fields

Every CSV row has 19 columns; every JSON entry additionally has `themes[]`, `added_in_version`, `relevance_to_foodberg`, `verified`, `acquired`.

**Fields new in v2**:

| Field | Values | Purpose |
|---|---|---|
| `Era` | `pre1900`, `1900_1945`, `1945_1980`, `1980_2010`, `2010_2020`, `2020_present`, `spanning` | Temporal filter |
| `Geography` | `US`, `US_Global`, `Global`, `Europe`, `Asia`, `LatAm`, `Africa`, `Colonial` | Geographic filter |
| `themes[]` | `supply`, `demand`, `technology`, `policy`, `labor`, `climate`, `trade`, `finance`, `methodology` | Multi-tag thematic filter |
| `added_in_version` | `v1`, `v2` | Lineage |

**New priority level**: `FLAGSHIP` — the single top canonical work per category (25 total, one per category). Rank above CRITICAL.

---

## 25 Categories

### v1 Carryover (14)

1. **Ag Econ Foundations** — price theory, supply response, futures, hedging, market structure
2. **US Commodity Policy** — Farm Bills, subsidies, biofuels policy, sugar/dairy, conservation
3. **Food Price History (Long-Run)** — pre-1900, 20c inflation, 1970s shock, 2008 crisis, 2011/2022 spikes, secular trends
4. **Cereals & Grains** — wheat, corn, rice, soybeans, CBOT, yield/weather
5. **Meat & Livestock** — beef, pork, poultry, packer concentration, feed costs, policy
6. **Dairy** — US policy, milk markets, global dairy, cheese/butter
7. **Oils & Fats** — palm, soy, canola/sunflower, olive, tropical cycles
8. **Sugar & Sweeteners** — cane/beet, HFCS, US sugar program, global sugar
9. **Produce** — seasonality, cold chain, labor, specialty crops, water–ag
10. **Global Food Systems** — Green Revolution, FAO FPI methods, food crises, food security, super-cycles
11. **Trade & Geopolitics** — WTO/Doha, NAFTA/USMCA, China, Russia–Ukraine, export bans
12. **Climate, Land & Inputs** — fertilizer, drought, climate-yields, energy–food, land use
13. **Chef / Restaurant Economics** — menu engineering, food-cost mgmt, vendor procurement, inflation pass-through, foodservice econ
14. **Data Source Methodology** — WASDE, CPI/PPI, FAO, WB, series construction

### New in v2 (11)

15. **Food Technology & Innovation** — mechanization, biotech, alt-protein, precision ag, vertical farming, digital ag
16. **Food Processing & Preservation** — canning, freezing, pasteurization, drying, irradiation, modified-atmosphere, extrusion/ultra-processing
17. **Supply Chain, Logistics & Cold Chain** — trucking, container shipping, rail history, cold chain, supermarket logistics, pandemic supply
18. **Retail & Grocery History** — chain-store era, supermarket rise, Walmart, Amazon/Whole Foods, food deserts, dollar stores, Kroger–Albertsons, meal kits, instant grocery
19. **Food & Ag Labor** — meatpacking labor, farmworker (Bracero/UFW), restaurant labor, H-2A & immigration, slavery/plantation
20. **Demand: Diet, Income, Consumption** — diet transition, Engel's Law, income elasticity, meat demand, obesity econ, dietary guidelines, GLP-1 demand shock, sugar consumption
21. **Food Safety & Regulation** — regulatory history, FDA/USDA, HACCP, recalls/outbreaks, pesticide regulation
22. **Nutrition, SNAP & Food Assistance** — SNAP history, Thrifty Food Plan, school lunch, WIC, food insecurity, commodity donations
23. **Non-Row-Crop Commodities** — coffee, cocoa, tea, spices, seafood/aquaculture, honey/pollinators, nuts
24. **Ag R&D, Extension & Institutions** — land-grant, CGIAR, foundations, extension service, productivity (TFP)
25. **Water, Irrigation & Soil** — Dust Bowl, reclamation, Ogallala, SGMA California, soil conservation

---

## Theme Tags (cross-cutting)

Used in the JSON `themes[]` array — independent of category. A single entry can have multiple themes.

| Theme | Count | Meaning |
|---|---:|---|
| `supply` | 379 | Production, yield, output economics |
| `policy` | 273 | Regulation, subsidies, institutional |
| `demand` | 190 | Consumption, income elasticity, diet |
| `technology` | 154 | Innovation, mechanization, biotech |
| `methodology` | 132 | Data construction, measurement, methods |
| `trade` | 131 | Imports, exports, tariffs, geopolitics |
| `finance` | 103 | Futures, speculation, credit, margins |
| `climate` | 103 | Weather, climate change, land, inputs |
| `labor` | 54 | Workers, wages, unions, migration |

---

## Priority Rubric v2

| Level | Share | Definition |
|---|---:|---|
| **FLAGSHIP** | 3.0% (25) | Single top canonical work per category |
| **CRITICAL** | 4.5% (37) | Foundational; without it, a core story cannot be told |
| **HIGH** | 44.7% (369) | Major contribution; covers a category in depth |
| **MEDIUM** | 38.3% (316) | Useful reference; strengthens a subcategory |
| **LOW** | 9.5% (78) | Tangential/duplicative, catalogued for completeness |

---

## Geographic Distribution

| Bucket | Count | Share |
|---|---:|---:|
| US | 470 | 56.9% |
| Global | 250 | 30.3% |
| US_Global | 45 | 5.5% |
| Asia | 32 | 3.9% |
| Europe | 14 | 1.7% |
| Africa | 7 | 0.8% |
| Colonial | 4 | 0.5% |
| LatAm | 3 | 0.4% |

US-primary (US + US_Global): 62.4%. Target was ≥65% — slightly under, but acceptable given legitimate global coverage in Cat 10, 11, 23.

## Temporal Distribution

| Era | Count | Share |
|---|---:|---:|
| 2020_present | 254 | 30.8% |
| 2010_2020 | 240 | 29.1% |
| 1980_2010 | 130 | 15.8% |
| spanning | 102 | 12.4% |
| 1945_1980 | 43 | 5.2% |
| pre1900 | 31 | 3.8% |
| 1900_1945 | 25 | 3.0% |

**Recent-trend coverage (2010_2020 + 2020_present) = 59.9%** — far exceeds the ≥25% plan target, reflecting the user's explicit ask for recent-trend depth.
