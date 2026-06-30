# Foodberg — Outputs

This directory holds deliverables and exports produced by the Foodberg project.

Foodberg is a **historical food-price explorer**: a full-stack web application
(React frontend + FastAPI backend) that harmonizes ~166,500 records from five
public data sources — USDA WASDE, FRED, BLS CPI, FAO, and the World Bank — plus
derived composite indices, into a single queryable SQLite database covering 50+
agricultural commodities. It runs locally and is not a deployed/hosted service.
See the root [`README.md`](../README.md) for setup, data-source record counts,
and provenance.

## Directory Structure

### Data/
Tabular data exported from the application or the underlying database
(e.g., commodity price series, index values). Source data is downloadable from
the public APIs listed in the root README; nothing here is canonical — the
canonical store is the backend SQLite database (`backend/data/foodberg.db`).

### Generated/
Miscellaneous generated files and exports produced by application or pipeline
scripts.

### Reports/
Generated analytics and report artifacts.

### KB Wishlist folders (`2026.* KB Wishlist*`)
Knowledge-base acquisition wishlists (v1–v4) used to plan source/document
acquisition for the project. These are working catalogs, not application output.

## Notes

- This README describes the **actual** project. Foodberg has no chef-facing
  SaaS dashboard, "Reports Center", vendor-comparison tool, menu-engineering
  workbook, or LaTeX executive/methodology PDFs — earlier versions of this file
  described a fictional product and have been replaced.
- Raw inputs live under the project's `Inputs/` directory (gitignored;
  re-downloadable from the public APIs).
