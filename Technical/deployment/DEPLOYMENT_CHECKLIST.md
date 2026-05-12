# Foodberg Deployment Checklist

## Pre-Deployment Status ✓

### Database Ready

- [x] **163,571 total records**
  - WASDE Agricultural Data: 147,369 records
  - Economic Indicators (FRED + BLS): 13,185 records
  - Global Food Prices (FAO): 3,017 records
- [x] Database backup created: `foodberg_backup_20251205.db` (199 MB)
- [x] Data collection system tested and working

### Backend Ready

- [x] FastAPI application with health check endpoint
- [x] Standalone data collectors (not dependent on Robin)
- [x] Database management utilities (backup, export, stats)
- [x] Production startup script (`start.py`)
- [x] Render deployment config (`render.yaml`)
- [x] Environment configuration (`.env.example`)

### Frontend Ready

- [x] React + Vite + TypeScript application
- [x] Netlify deployment config (`netlify.toml`)
- [x] API proxy configuration for backend

---

## Deployment Steps

### 1. Backend to Render

1. **Push to GitHub**

   ```bash
   cd 
   git add .
   git commit -m "Foodberg deployment ready"
   git push origin main
   ```

2. **Create Render Web Service**
   - Go to <https://dashboard.render.com>
   - New → Web Service
   - Connect GitHub repository
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables** (in Render dashboard)

   ```
   FRED_API_KEY=***REMOVED***
   BLS_API_KEY=44ebd49f0bc54feb83b2e452e6b123b2
   USDA_API_KEY=***REMOVED***
   CORS_ORIGINS=https://foodberg.org,https://www.foodberg.org
   ENV=production
   ```

4. **Upload Database** (First deployment only)
   - The SQLite database needs to be included in the deployment
   - Or use the data collection on first startup

### 2. Frontend to Netlify

1. **Create Netlify Site**
   - Go to <https://app.netlify.com>
   - Add new site → Import from Git
   - Connect GitHub repository
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`

2. **Set Environment Variables**

   ```
   VITE_API_URL=https://foodberg-api.onrender.com
   ```

3. **Configure Custom Domain**
   - Add custom domain in Netlify settings
   - Update Namecheap DNS:
     - A record: `@` → Netlify IP
     - CNAME: `www` → `yoursite.netlify.app`

---

## File Structure for Deployment

```
Foodberg/
├── backend/                    # Deploy to Render
│   ├── main.py                 # FastAPI app
│   ├── start.py                # Production startup
│   ├── data_pipeline.py        # Data collection CLI
│   ├── db_management.py        # Backup/export utilities
│   ├── requirements.txt        # Python dependencies
│   ├── render.yaml             # Render config
│   ├── Procfile                # Process definition
│   ├── .env.example            # Environment template
│   ├── config/
│   │   └── api_keys.json       # Local API keys (gitignored)
│   ├── data/
│   │   ├── foodberg.db         # SQLite database (199 MB)
│   │   ├── collected/          # Collected JSON data
│   │   ├── backups/            # Database backups
│   │   └── exports/            # CSV exports
│   ├── database/               # SQLAlchemy models & importers
│   ├── data_sources/           # API clients & collectors
│   ├── ai/                     # AI substitution engine
│   ├── ml/                     # Price prediction models
│   └── vendors/                # Vendor price parsing
│
├── frontend/                   # Deploy to Netlify
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── stores/
│   ├── netlify.toml            # Netlify config
│   ├── package.json
│   └── vite.config.ts
│
├── Inputs/                     # Historical price data
├── Technical/                  # Development docs
├── Outputs/                    # Generated reports
└── DEPLOYMENT_GUIDE.md         # Full deployment docs
```

---

## API Keys Reference

Located in `

| Service | Key | Source |
|---------|-----|--------|
| FRED | `***REMOVED***` | `[2025.09.28] api_keys.json` |
| BLS | `44ebd49f0bc54feb83b2e452e6b123b2` | `[2025.09.28] api_keys.json` |
| USDA NASS | `***REMOVED***` | `usda_nass.json` |
| BEA | `857E9ADD-656E-43ED-9598-4EA83299418F` | `[2025.09.28] api_keys.json` |

---

## Verification Commands

```bash
# Check database status
cd backend && python data_pipeline.py status

# Create backup
python db_management.py backup

# Export to CSV
python db_management.py export

# Test API locally
python -m uvicorn main:app --reload
# Then visit: http://localhost:8000/docs
```

---

## Post-Deployment Checklist

- [ ] Backend health check passing: `https://foodberg-api.onrender.com/api/health`
- [ ] Frontend loading: `https://foodberg.org`
- [ ] API proxy working: Test price endpoints
- [ ] SSL certificates active
- [ ] Data refresh scheduled (optional cron job)

---

*Last updated: December 5, 2025*
