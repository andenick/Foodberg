# HANDOFF — Robert PDF Library v2.0 Sync

**Date**: 2026-05-25
**Project**: Foodberg
**Operation**: v2.0 migration (project-folder-flat + content-type symlinks)
**Operator**: Claude Opus 4.7 [1m]

## Summary

- Files moved into `_PDF_LIBRARY/Foodberg/`: **760**
- Files already at v2.0 location: 0
- Total disk in project folder: 6.25 GB
- Content-type symlinks created in `_PDF_LIBRARY/_BY_CONTENT_TYPE/`:
  - `Books_General`: 759
  - `Filings_Regulatory`: 1

## Convention

- Primary store: `_PDF_LIBRARY/Foodberg/` (flat, one canonical copy per file)
- Symlink library: `_PDF_LIBRARY/_BY_CONTENT_TYPE/<type>/` (zero disk cost grouping)
- Filename styles coexist: `<wl_id>__<title>__<source>.pdf` (curated wishlist) + `[YYYY]__Author__Title__hash.pdf` (bulk-library)

## Registry status

- `_UNIFIED/PROJECT_REGISTRY.json`: entry present with `convention: v2.0_dual_naming`
- `_UNIFIED/PDF_REGISTRY.csv`: `canonical_name` updated to `Foodberg/<filename>` for migrated files
- `_UNIFIED/RENAME_LEDGER.csv`: append-only audit row per move (reversible)

## References

- Standard: `Council/Druck/docs/ROBERT_PDF_LIBRARY_V2_STANDARD.md`
- Convention spec: `Council/Robert/Knowledge_Base/_PDF_LIBRARY/README.md`
- Migration report: `Council/Robert/Knowledge_Base/_UNIFIED/_integration_audit/ROBERT_PDF_LIBRARY_V2_MIGRATION_REPORT_2026-05-25.md`
- Sync skill: `/robert-pdf-sync Foodberg` (`.claude/skills/robert-pdf-sync.md`)

## Action items (next session)

- [ ] (Optional) Run HDARP campaign on this project's PDFs if KB extraction not yet done
- [ ] (Optional) Future GPU rename to unified `<wl_id>__<title>__<source>` per `GPU_NAMING_PIPELINE_PLAN.md`
