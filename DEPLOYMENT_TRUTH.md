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
- `backend/data/foodberg.db` — see the warning immediately below.

## 5. ⚠️ Open production exposure (requires a human decision)

**The 70 fabricated `retail_prices` rows deleted on 2026-07-24 are still being served by
the live site.** The deletion was applied to the canonical database at
`Projects/Foodberg/backend/data/foodberg.db`. Production serves the database **baked into
the running image**, which was built from `deploy/foodberg/backend/data/foodberg.db` and
still contains all 70 rows. They clear only when the backend image is rebuilt and
recreated per §3, which is deliberately **not** done by the P0 work.

Nothing else in the P0 batch (P0-4 FAO honesty, P0-5 unfrozen tables) reaches production
either, for the same reason. All of it ships together on the next reviewed deploy.

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
