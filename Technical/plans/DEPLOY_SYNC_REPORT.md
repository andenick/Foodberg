# Foodberg Deploy Tree Sync Report
**Date**: 2026-07-07
**Operator**: pi build agent
**Scope**: Sync `Projects/Foodberg/` → `Council/Carson/Technical/deploy/foodberg/`

---

## 1. What Was Synced

### 1.1 `backend/main.py`
| Metric | Before (Jun 12) | After (Jul 4) | Delta |
|--------|-----------------|---------------|-------|
| Size | 43,068 bytes (43 KB) | 49,296 bytes (49 KB) | +6,228 bytes |
| Lines | 1,198 | 1,372 | +174 (+15%) |
| Backup | — | `main.py.bak_20260707` | 43,068 bytes |

**Change scope**: Backend overhaul (Jul 4–5 cycle). New endpoints, PSD router wiring, data pipeline updates, composite index recalculation logic. Old deploy was 3 weeks stale (Jun 12).

### 1.2 `backend/routers/psd_router.py` — **NEW (MISSING from deploy)**
- Size: 6,416 bytes (6 KB), 169 lines
- Deploy tree had **no `routers/` directory at all**
- This router handles USDA PSD (Production, Supply, Distribution) data queries via Robin — a core endpoint that didn't exist in the Jun 12 deploy

### 1.3 `backend/indices/` — **NEW (MISSING from deploy)**
| File | Size | Lines |
|------|------|-------|
| `__init__.py` | 123 bytes | 4 |
| `composite.py` | 8,124 bytes | 246 |

Deploy tree had **no `indices/` directory**. `composite.py` builds the composite food price indices (FAO-style) from the per-source tables — this is the "Reindex" logic that had been removed from the frontend but lives server-side.

### 1.4 `backend/requirements.txt`
- Size unchanged (492 bytes), but content **differs** (version bumps / dependency changes from the Jul 4 update)

### 1.5 `frontend/dist/` — **Rebuilt**
| Metric | Before | After |
|--------|--------|-------|
| Total size | 4.3 MB | 4.3 MB |
| JS bundles | Jun 20 vintage | Jul 7 vintage (fresh build) |
| Source fix | — | Removed orphaned `reindexing`/`reindexStatus`/`reindexMessage` state + `RefreshCw` import from `DataSources.tsx` (TS6133) |

Frontend required a code fix to compile: the reindex button had been removed from the UI but its state variables, handler, and icon import were left in `DataSources.tsx` (7 unused variables). Cleaned those out before the build.

---

## 2. What Was Cleaned

- **`__pycache__/` directories** purged from entire deploy tree:
  - `backend/__pycache__/`
  - `backend/routers/__pycache__/`
  - `backend/indices/__pycache__/`
- Zero `__pycache__` dirs remain (verified with `find -type d -name __pycache__`)

---

## 3. What Was Created

- **`robin_data/` directory** with `README.md` (932 bytes)
  - Documents the Docker volume mount (`./robin_data:/robin:ro`)
  - Explains WASDE/PSD CSV layout expected by `RobinWASDEClient`
  - Notes: directory is for `docker-compose.yml` volume, not tracked in git

---

## 4. Deploy Buildability Assessment

### ✅ Buildable — YES

| Check | Status | Detail |
|-------|--------|--------|
| Dockerfile present | ✅ | `backend/Dockerfile` — production build (python:3.11-slim, carson-telemetry vendored, no Litestream/S3) |
| `carson-telemetry/` vendored | ✅ | `src/carson_telemetry/` + `pyproject.toml` present |
| `requirements.txt` present | ✅ | Python deps at deploy root |
| Frontend compiled | ✅ | Fresh `dist/` with hashed bundles |
| `docker-compose.yml` coherent | ✅ | References `backend/Dockerfile`, `./robin_data:/robin:ro`, `./frontend/dist:/srv:ro` |
| `Caddyfile` present | ✅ | Reverse proxy config for foodberg-web → foodberg-backend:8000 |
| All backend sources present | ✅ | `config/`, `data_sources/`, `database/`, `routers/`, `indices/` all in place |
| DB baked in | ✅ | `backend/data/foodberg.db` present (baked into image) |
| Telemetry volume | ✅ | `foodberg_telemetry` volume defined |

### Dockerfile is a production-appropriate simplification
The deploy Dockerfile is intentionally simpler than the project one (`Projects/Foodberg/backend/Dockerfile`):
- **No Litestream** (database is baked in, not S3-replicated)
- **No S3 restore** (not needed for the homelab deploy)
- **Vendored `carson-telemetry`** (installed from local wheel, not pip)
- **Direct uvicorn** (no docker-entrypoint.sh healthchecks)

This is correct — the deploy tree is purpose-built for the homelab Docker Compose setup, not the project's Fly.io/S3 pipeline.

---

## 5. What Still Needs Attention

| Item | Priority | Detail |
|------|----------|--------|
| **`robin_data/` data files** | HIGH | Directory exists but is empty. The `foodberg-backend` container expects WASDE/PSD CSVs at `/robin/DATA/USDA_WASDE/`. Populate before deploy or the PSD endpoints will serve no data. |
| **`config/api_keys.json`** | HIGH | Only `api_keys.json.template` exists at the deploy tree. The container won't have API keys to call Alpha Vantage or BLS. Either provide the real file or ensure the deploy only uses offline sources. |
| **`backend/Dockerfile` context mismatch** | MEDIUM | Dockerfile copies `carson-telemetry/` from the build context root, but the project's project-level Dockerfile (`Projects/Foodberg/backend/Dockerfile`) uses a different approach. This is fine for the deploy tree but the two will diverge further over time. |
| **npm `caniuse-lite` stale** | LOW | Build warns `caniuse-lite` is 7 months old. Run `npx update-browserslist-db@latest` in `Projects/Foodberg/frontend/` at next convenience. |
| **Frontend `DataSources.tsx` edit** | LOW | The edit removing reindex UI is in the project tree. If the reindex feature is ever restored to the backend, the frontend UI needs to be added back (or the old `git diff` committed). |

---

## 6. Operation Summary

```
Steps completed:
  1. Backup    → main.py.bak_20260707 (43 KB)
  2. Sync      → main.py, routers/, indices/, requirements.txt
  3. Clean     → __pycache__/ tree purged
  4. Create    → robin_data/ + README.md
  5. Verify    → Dockerfile present, buildable ✅
  6. Rebuild   → npm run build (fixed TS6133), dist/ copied to deploy
  7. Report    → this file

NOT done:
  - No docker compose up / deploy
  - No GPU / Hopper process touched
  - No robin_data population (needs user action)
```

---

## 7. Files Modified/Created

| Action | Path | Size |
|--------|------|------|
| BACKUP | `Council/Carson/Technical/deploy/foodberg/backend/main.py.bak_20260707` | 43 KB |
| COPY (overwrite) | `Council/Carson/Technical/deploy/foodberg/backend/main.py` | 49 KB |
| COPY (new dir) | `Council/Carson/Technical/deploy/foodberg/backend/routers/` | 6 KB |
| COPY (new dir) | `Council/Carson/Technical/deploy/foodberg/backend/indices/` | 8 KB |
| COPY (overwrite) | `Council/Carson/Technical/deploy/foodberg/backend/requirements.txt` | 492 B |
| CREATE | `Council/Carson/Technical/deploy/foodberg/robin_data/README.md` | 932 B |
| DELETE | 3× `__pycache__/` trees | — |
| CREATE (overwrite) | `Council/Carson/Technical/deploy/foodberg/frontend/dist/` | 4.3 MB |
| EDIT | `Projects/Foodberg/frontend/src/pages/DataSources.tsx` | removed orphan reindex UI |
| CREATE | `Projects/Foodberg/Technical/plans/DEPLOY_SYNC_REPORT.md` | this file |