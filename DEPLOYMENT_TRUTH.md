# Foodberg — Deployment Truth

**Authoritative as of 2026-07-24.** Supersedes every other deployment document in this
repository. If another file disagrees with this one, this one is right and the other is
dead (see "Dead configurations" below).

---

## 1. Where each half lives

| Half | Canonical location | Notes |
|---|---|---|
| **Frontend source** | `Projects/Foodberg/frontend/src/` | Vite + React + TypeScript |
| **Frontend build artifact** | `Projects/Foodberg/frontend/dist/` | Produced by `npm run build`. **Matches live production.** |
| **Backend application** | `Projects/Foodberg/backend/` | FastAPI. `main.py`, `routers/`, `database/`, `indices/`, `data_sources/` |
| **Application database** | `Projects/Foodberg/backend/data/foodberg.db` | ~1.6 GB SQLite, git-ignored. Rebuilt by `backend/database/rebake_history.py` |
| **Deployment configuration** | `Council/Carson/Technical/deploy/foodberg/` | `docker-compose.yml`, `Caddyfile`, `backend/Dockerfile`, `carson-telemetry/`, `robin_data/` |

**One rule:** `Projects/Foodberg/` is canonical for **both** application halves.
`Council/Carson/Technical/deploy/foodberg/` is a **deploy mirror plus deployment
configuration**. Application code and built assets are never authored there — they are
copied in from the project tree immediately before a deploy.

## 2. What actually runs in production

Foodberg runs on the **Carson mini PC**. Not Netlify. Not Render. Not Vercel.

```
Internet
  └─ Cloudflare tunnel (id b33251e0-…, andenick-sites)
       └─ foodberg-web        caddy:2.8.4-alpine, serves /srv, proxies /api/* → backend
       └─ foodberg-backend    image foodberg-backend:1.0.0, uvicorn main:app :8000
     both on docker network `homelab_default`
```

Compose file: `Council/Carson/Technical/deploy/foodberg/docker-compose.yml`.

**The two halves reach production by different mechanisms, and this is the single most
important fact on this page:**

| Half | Mechanism | Consequence |
|---|---|---|
| **Frontend** | `./frontend/dist` is **bind-mounted read-only** into `foodberg-web:/srv` | A file written into `deploy/foodberg/frontend/dist/` is **live immediately**. No rebuild, no restart, no confirmation step. Treat any write there as a production deploy. |
| **Backend + database** | `backend/Dockerfile` does `COPY backend/ /app/`, so the code **and the 1.6 GB `foodberg.db` are baked into the image** | Editing `deploy/foodberg/backend/**` changes nothing until the image is rebuilt. It changes everything on the next `docker compose build`. |

## 3. How a deploy is actually performed

Run on the box that hosts the containers, from
`Council/Carson/Technical/deploy/foodberg/`.

```bash
# 0. PRE-FLIGHT — refuse to deploy on a dirty or unreconciled tree
git -C <project>/Foodberg status --short          # expect clean
diff <project>/Foodberg/backend/main.py deploy/foodberg/backend/main.py

# 1. Build the frontend from canonical source
cd <project>/Foodberg/frontend && npm ci && npm run build

# 2. Sync BOTH halves project → deploy mirror (project is the source, always)
rsync -a --delete <project>/Foodberg/frontend/dist/  deploy/foodberg/frontend/dist/
rsync -a --delete --exclude venv --exclude __pycache__ --exclude logs \
      --exclude .env --exclude config/api_keys.json \
      <project>/Foodberg/backend/  deploy/foodberg/backend/
#    ^ step 2's first rsync is ALREADY a frontend deploy (bind mount). Expect it.

# 3. Rebuild + restart the backend (this is what ships backend code and the DB)
cd deploy/foodberg
docker compose build foodberg-backend
docker compose up -d --force-recreate foodberg-backend

# 4. Smoke test against a real data endpoint, not just /
curl -s localhost/api/health
curl -s localhost/api/indices/fao_overall | head -c 300
curl -s "localhost/api/prices/search?commodity=tomato" | head -c 300
```

**Never** run `docker compose up -d --force-recreate` from the deploy tree without doing
step 2 first. That was the live regression hazard recorded as P0-1: the deploy tree's
frontend `dist/` was 13 days stale (2026-07-07) relative to production (2026-07-20), so a
routine recreate would have rolled the site back and removed the Legacy (1979–2009) tab.

## 4. Reconciliation performed 2026-07-24 (P0-1)

Before this date neither tree was a superset of the other.

| Item | Before | After |
|---|---|---|
| `backend/routers/wasde_vintages_router.py` | present **only** in deploy tree | copied into the project tree; the two files are byte-identical |
| `backend/main.py` router mounts | deploy tree carried 8 extra lines mounting `wasde_vintages_router` + `wasde_legacy_router` | project `main.py` now carries them; `diff --strip-trailing-cr` between the trees is **empty** |
| `frontend/dist/` | deploy copy stale (2026-07-07, md5 `a795dd5a`, 2,167 B, no `downloads/`, no `llms.txt`) | **left untouched on purpose** — writing it is a live deploy. Project tree is declared canonical; the mirror is refreshed at deploy time by step 2 above. |
| `domains_registry.json` | claimed `deploy/foodberg/frontend/dist` "is the built artifact" | corrected; now names `Projects/Foodberg/` canonical for both halves and points here |

The deploy tree was **not deleted**. It remains intact and is now explicitly scoped to
deployment configuration plus a refresh-on-deploy mirror.

### Still divergent, and deliberately so

These project-tree files differ from the deploy mirror and should **not** be blindly
synced backwards:

- `backend/database/rebake_history.py` — the project copy resolves Robin's data store from
  `$ROBIN_DATA_PATH` with a relative fallback. The deploy copy hardcodes an absolute
  workspace path. The env-var form is correct; hardcoding it in a file that ships in a
  public repo is a publication-hygiene leak.
- `backend/indices/composite.py` — the project copy carries the P0-4 fix (FAO's published
  index served under FAO's name). The deploy copy still recomputes it.
- `backend/data/foodberg.db` — see §5.

> **Note added 2026-07-24 (post-deploy):** this table describes the *workstation staging mirror*
> at `Council/Carson/Technical/deploy/foodberg/`, which was **not** updated by the deploy and is
> now stale in both halves. It is not what production runs. For the divergence that actually
> matters — project tree vs **the box** — see the hazard table in §5.

## 5. ✅ P0 SHIPPED — deployed to production 2026-07-24

**Status: CLOSED.** The exposure recorded here (fabricated rows served live) was cleared by a
reviewed deploy on **2026-07-24 ~18:18 EDT**, after PR #1 was merged to `master` as
**`cd4568f`**. What is now live:

| Defect | Before (live) | After (live, verified) |
|---|---|---|
| P0-3 fabricated rows | `retail_prices` = **20,429**; `/api/prices/search?commodity=saffron&sources=retail` returned `saffron $2.85 source "USDA"` (also truffle $2.15, lobster $2.71) | `retail_prices` = **20,359**; saffron / truffle / lobster / "Tomato powder" all return **0 hits**; `tomato` returns 100 real **BLS AP** rows (latest 2026-06 = **$2.154/lb**) |
| P0-4 FAO honesty | `fao_overall` 2025-11 = **124.5**, a Foodberg recomputation labelled FAO | `fao_overall` 2025-11 = **125.1**, FAO's published figure, `components_json` = `{"series":"published","publisher":"FAO","recomputed":false}`. The recomputation now ships separately as **`foodberg_global_composite`** |
| P0-5 frozen tables | `composite_indices` = 2,715 rows, `computed_at` uniformly **2026-03-28** | `composite_indices` = **3,146** rows, `computed_at` **2026-07-24T21:36:44** |
| P0-6 liveness (S5) | `apples`→BLS retail served as current with no staleness marker; `strawberries`→dead mapping returning zero rows | every series in `/api/prices/coverage` now carries a `liveness` block (53 live / 12 stale / 5 discontinued); `apples` retail is `discontinued, 104 months behind`; the dead `strawberries` retail mapping is gone |

### How it was actually deployed (correcting §3)

§3's "run on the box … from `Council/Carson/Technical/deploy/foodberg/`" is misleading. The
containers do **not** run on the workstation. They run on the **HP EliteDesk 800 G5 at
`192.168.0.174`** (Ubuntu + Docker), in `~/sites/foodberg/`. The workstation path
`Council/Carson/Technical/deploy/foodberg/` is a *third* copy — a staging mirror — and it is
**stale in both halves**. The real deploy is `scp` from the project tree to the box, then
`docker compose build` + `up -d --force-recreate foodberg-backend` **on the box**.

What shipped, and only this (a surgical delta, not a tree sync):

```
scp Projects/Foodberg/backend/indices/composite.py             -> box:~/sites/foodberg/backend/indices/
scp Projects/Foodberg/backend/data_sources/worldbank_client.py -> box:~/sites/foodberg/backend/data_sources/
scp Projects/Foodberg/backend/database/rebake_history.py       -> box:~/sites/foodberg/backend/database/
scp Projects/Foodberg/backend/data/foodberg.db  (1.64 GB, md5 0b7373fb4665...)
                                                               -> box:~/sites/foodberg/backend/data/
ssh box 'cd ~/sites/foodberg && docker compose build foodberg-backend \
                             && docker compose up -d --force-recreate foodberg-backend'
```

`foodberg-web` was **not** touched (it stayed up 4 weeks through the deploy). No other
container on the box was touched.

### ✅ RESOLVED 2026-07-24 — the project tree vs the box (was: five divergent backend files)

`Projects/Foodberg/backend/` was **not** a superset of what production runs. P0-1 reconciled the
project tree against the *workstation staging mirror*; nobody had compared it against **the box**.
Byte-comparison on 2026-07-24 (CRLF-normalised) found `main.py`, `database/manager.py` and both
WASDE routers identical, but five files differed. **All five are now reconciled**, plus the
box-only `routers/__init__.py`:

| File | Divergence found | Resolution (2026-07-24) |
|---|---|---|
| `data_sources/fred_client.py` | box was **offline, local-DB backed** (no outbound HTTP, no `FRED_API_KEY`); project tree carried the old **online** version calling `api.stlouisfed.org` via `httpx` | ✅ **box version pulled into the project tree.** md5 `0d3d5a074fa2dd01d5edff872bd1d388` on both ends. Syncing the old project copy would have broken economic indicators in a container that has no FRED key |
| `data_sources/fao_client.py` | box carried a later offline rewrite with the mock generators deleted; project tree had the 2026-07-04 DB-query version | ✅ **box version pulled into the project tree.** md5 `3c3af71c0955b186ccb22a3db64f8b06` on both ends |
| `database/models.py` | project ahead — adds the `WasdePsd` model (additive, unshipped) | ✅ project stays ahead **by design**; ships with the next backend image build. Additive only — no box behaviour depends on its absence |
| `database/collect_live.py` | project ahead — prefixes `"Alpha Vantage - "` on commodity names (unshipped) | ✅ project stays ahead **by design**. This is a live-collection path, not a serving path; it does not run inside the container |
| `data_sources/robin_client.py` | import reorder only | ✅ cosmetic; no action. Not a functional divergence |
| `routers/__init__.py` | existed **on the box** (0 bytes) and **not** in the project tree | ✅ created in the project tree as a 0-byte file, matching the box |

**Verification after reconciliation:** `python -c "import main"` from `backend/` succeeds and the app
registers **58 routes** (57 before `/api/download/{dataset}.xlsx` was added).

**The rule still stands: never `rsync --delete` the project backend onto the box.** Two files in
§4's "still divergent, and deliberately so" list (`rebake_history.py`, `indices/composite.py`) and
the 1.6 GB `foodberg.db` make a blanket sync destructive. Deploy the specific files a change
touches, md5-verifying both ends, exactly as §5 records.

> **Also note:** `backend/data/foodberg.db` is in **WAL mode**. Run
> `PRAGMA wal_checkpoint(TRUNCATE)` before copying it to the box — otherwise recent writes sit in
> `foodberg.db-wal` and do not travel with the `.db` file.

### Rollback point for the 2026-07-24 deploy

Still on the box, nothing pruned:

- image `foodberg-backend:rollback-20260720` = `7685f4bd180f` (the pre-deploy image; the
  `1.0.0` tag was overwritten by the rebuild and is now `bb0f1ed53f53`)
- `~/sites/foodberg_rollback_20260724/` = pre-deploy `composite.py`, `worldbank_client.py`,
  `rebake_history.py`, and `foodberg.db.rollback_20260720` (1,637,339,136 B)

```bash
ssh andenick@192.168.0.174 \
  'cd ~/sites/foodberg && docker rm -f foodberg-backend \
   && docker tag foodberg-backend:rollback-20260720 foodberg-backend:1.0.0 \
   && docker compose up -d --no-build foodberg-backend'
```

That restores the exact pre-deploy image (code **and** DB, both baked in) without touching the
source tree or `foodberg-web`. Retire the rollback artifacts only once this deploy has been
observed healthy for a while.

## 6. Dead configurations — do not follow

Checked into this repository but non-functional. They exist for history only.

| File | Why it is dead |
|---|---|
| `frontend/netlify.toml` | Foodberg is not on Netlify; the URL 404s |
| `backend/render.yaml` | Not on Render; 404 with `x-render-routing: no-server` |
| `backend/Procfile` | Heroku-style; nothing consumes it |
| `backend/Dockerfile` + `backend/litestream.yml` | **Cannot build** — its `ENTRYPOINT` names a file that does not exist. The real image builds from `deploy/foodberg/backend/Dockerfile` |
| `Technical/deployment/*` | A third, nginx-based model. Its guide instructs `A @ 75.2.60.5` — **following it would take the live site down** |

## 7. Secrets

No credential belongs in this repository, in the deploy tree, in a commit, or in a log.

- `backend/config/api_keys.json` and `backend/.env` are git-ignored and must stay so.
- The USDA AMS MARS key lives in the operating system's credential vault and is read at
  runtime via `keyring.get_password(...)`. It must never be written to a file, a commit,
  an environment file, or a log. The vault entry name is recorded in the internal
  operations notes, not here.
- Run `gitleaks detect` before every push.
