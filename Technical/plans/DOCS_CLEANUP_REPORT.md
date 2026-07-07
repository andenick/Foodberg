# Foodberg Cleanup Report — 2026-07-07

## Changes

### 1. Rewrote `.claude/instructions.md`
- Replaced the stale Druck v1.1 template (Oct 2025) that described Foodberg as a fictional
  "Professional food cost management platform for chefs" with Sysco/US Foods APIs, AI features,
  menu engineering, and vendor comparisons.
- New file is a clean, honest, 66-line agent config reflecting what Foodberg actually is:
  a live Historical Food Price Explorer at foodberg.org, part of the Heterodata ecosystem.
- Removed all "Nick" references per publication hygiene.

### 2. Moved `_patch_main_psd.py` to `Technical/scripts/`
- From: `_patch_main_psd.py` (project root)
- To:   `Technical/scripts/_patch_main_psd.py`

### 3. Consolidated archives
- Moved all 10 files from `_archive/` into `archive/Legacy_Handoffs_2025/`
- Deleted the empty `_archive/` directory
- Archive now has 3 organized subdirectories: `Legacy_Handoffs_2025/`, `Old_Documentation_2025-10-23/`,
  and `pre_reorganization_backup_20251003_113920/`

### 4. Added `Knowledge_Base/` to `.gitignore`
- Knowledge Base will be populated by Hopper integration — should not be in git

### 5. Removed Ghostscript bloat from `Technical/HDARP_Processing/`
- Deleted `gs_installer.exe` (Windows Ghostscript installer)
- Deleted `gs_portable/` directory (~151 MB, 100+ files of Ghostscript distribution)
- Freed approximately 152 MB

### 6. Moved 3 stale JS scripts to archive
- `Technical/scripts/[2025.09.25] collect-data.js`       → `archive/Legacy_Scripts_2025/`
- `Technical/scripts/[2025.09.25] download-free-data.js`   → `archive/Legacy_Scripts_2025/`
- `Technical/scripts/[2025.09.25] enhanced-bulk-collection.js` → `archive/Legacy_Scripts_2025/`

### 7. Fixed port mismatch in `frontend/.env.development`
- Changed `VITE_API_URL=http://localhost:8002` → `http://localhost:8000`
- Matches backend `.env.example` (`PORT=8000`)

### 8. Copied `backend/.env.example` → `backend/.env`
- Backend now has an env file for local development (all keys are placeholder values)

## Verification
- All moves confirmed via shell output
- `.gitignore` updated with `Knowledge_Base/` entry
- No remaining stale files in project root
- Ports now consistent (8000 throughout)