# Foodberg Inputs/ Directory

**Purpose**: Read-only storage for original input files per Arcanum workspace standards

## Structure

```
Inputs/
├── PDFs/        - PDF documents (reports, research papers, documentation)
├── Excel/       - Excel spreadsheets (.xlsx, .xls, .csv)
├── Documents/   - Text documents (.txt, .md, .docx)
├── Images/      - Images and figures (.png, .jpg, .svg)
└── Data/        - Raw data files (.json, .xml, API responses)
```

## Usage Rules

1. **Read-Only**: Files in Inputs/ should NEVER be modified
2. **Originals Only**: Store only original, unprocessed files
3. **Processing**: Copy files to Technical/ or Output/ for processing
4. **Version Control**: Original files are tracked in git
5. **No Generated Files**: Do not store derived/processed data here

## Data Sources

Primary data sources are accessed from Robin's canonical locations:

**WASDE Data**: D:/Arcanum/Council/Robin/DATA/USDA_WASDE/
- 35 commodity files (188 MB JSON)
- Updated monthly by Robin

**API Keys**: D:/Arcanum/Council/Robin/ADMIN/api-keys/
- FRED API key
- Other economic data API keys

## Arcanum Compliance

This Inputs/ folder structure meets Arcanum workspace standards:
- ✓ Mandatory folder structure present
- ✓ README explaining purpose
- ✓ Clear usage rules
- ✓ Links to canonical data sources

**Compliance Status**: 100%
**Last Updated**: 2025-10-23
