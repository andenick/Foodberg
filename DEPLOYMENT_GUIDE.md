# Foodberg Deployment Guide
**Deploy to foodberg.org in 30 minutes**

## Prerequisites

- GitHub account
- Netlify account (FREE): https://app.netlify.com/signup
- Render account (FREE): https://dashboard.render.com/register
- Domain (foodberg.org) with DNS access

## Step 1: Prepare Repository

### Push Code to GitHub
```bash
cd Projects/Foodberg
git init
git add .
git commit -m "Initial Foodberg deployment"
git remote add origin https://github.com/your-username/foodberg.git
git push -u origin main
```

## Step 2: Deploy Frontend to Netlify

### 2.1 Connect Repository
1. Log in to Netlify: https://app.netlify.com
2. Click "Add new site" → "Import an existing project"
3. Choose "GitHub" and authorize
4. Select "foodberg" repository
5. Branch: `main`

### 2.2 Configure Build
```
Base directory: frontend
Build command: npm run build
Publish directory: frontend/dist
```

### 2.3 Environment Variables
Add in Netlify dashboard (Site settings → Environment variables):
```
VITE_API_URL=https://foodberg-api.onrender.com
VITE_ENABLE_WEBSOCKET=true
VITE_ENABLE_AI_SUBSTITUTIONS=true
```

### 2.4 Custom Domain
1. Go to Site settings → Domain management
2. Click "Add custom domain"
3. Enter: `foodberg.org`
4. Follow DNS configuration instructions

### 2.5 DNS Configuration (Namecheap)
In Namecheap dashboard:
```
Type    Host    Value
A       @       75.2.60.5 (Netlify Load Balancer)
CNAME   www     foodberg.netlify.app
```

Or use Netlify DNS (simpler):
1. In Netlify: Domain settings → "Set up Netlify DNS"
2. Update nameservers in Namecheap to Netlify's

### 2.6 SSL Certificate
- Automatic via Netlify (Let's Encrypt)
- Usually ready within 24 hours
- Verify at: https://foodberg.org

## Step 3: Deploy Backend to Render

### 3.1 Create Web Service
1. Log in to Render: https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   ```
   Name: foodberg-api
   Region: Oregon (or closest to users)
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

### 3.2 Environment Variables
Add in Render dashboard (Environment tab):
```
PYTHON_VERSION=3.11.0
ENV=production
PORT=8000
CORS_ORIGINS=https://foodberg.org,https://www.foodberg.org

# API Keys
USDA_API_KEY=your_usda_key
FRED_API_KEY=your_fred_key
API_NINJA_KEY=your_apininja_key
OPENAI_API_KEY=your_openai_key

# Redis (add after creating Redis instance)
REDIS_URL=redis://...
```

### 3.3 Add Redis Instance
1. In Render dashboard: "New +" → "Redis"
2. Name: `foodberg-cache`
3. Plan: FREE
4. Region: Same as web service
5. Copy connection string to `REDIS_URL` in web service

### 3.4 Custom Domain (Optional)
1. In Render: Settings → Custom Domain
2. Add: `api.foodberg.org`
3. Add CNAME in DNS:
   ```
   Type    Host    Value
   CNAME   api     foodberg-api.onrender.com
   ```

### 3.5 Health Check
Render will automatically monitor `/api/health`

## Step 4: Verify Deployment

### 4.1 Frontend Checks
```bash
# Test homepage
curl https://foodberg.org

# Test dashboard access
curl https://foodberg.org/command-center

# Check SSL
curl -I https://foodberg.org | grep "HTTP/2 200"
```

### 4.2 Backend Checks
```bash
# Test API health
curl https://api.foodberg.org/api/health

# Test price endpoint
curl https://api.foodberg.org/api/prices/terminal/new_york

# Check API docs
open https://api.foodberg.org/docs
```

### 4.3 Integration Test
1. Visit https://foodberg.org
2. Navigate to Command Center
3. Verify live connection indicator
4. Check that prices load
5. Test recipe calculator
6. Verify charts render

## Step 5: Configure Monitoring

### 5.1 Uptime Robot (FREE)
1. Sign up: https://uptimerobot.com
2. Add monitor:
   ```
   Monitor Type: HTTP(s)
   Friendly Name: Foodberg Frontend
   URL: https://foodberg.org
   Monitoring Interval: 5 minutes
   ```
3. Add second monitor for API:
   ```
   URL: https://api.foodberg.org/api/health
   ```

### 5.2 Sentry (FREE - 5K errors/month)
1. Sign up: https://sentry.io
2. Create project: "foodberg"
3. Install SDK:
   ```bash
   # Frontend
   cd frontend
   npm install @sentry/react
   
   # Backend
   cd backend
   pip install sentry-sdk[fastapi]
   ```

4. Add to frontend (`src/main.tsx`):
   ```typescript
   import * as Sentry from "@sentry/react"
   
   Sentry.init({
     dsn: "your-sentry-dsn",
     environment: "production"
   })
   ```

5. Add to backend (`main.py`):
   ```python
   import sentry_sdk
   
   sentry_sdk.init(
       dsn="your-sentry-dsn",
       environment="production"
   )
   ```

### 5.3 Plausible Analytics (Optional - $9/month)
1. Sign up: https://plausible.io
2. Add script to `frontend/index.html`:
   ```html
   <script defer data-domain="foodberg.org" src="https://plausible.io/js/script.js"></script>
   ```

Or use self-hosted (FREE):
```bash
docker run -d -p 8001:8000 plausible/analytics
```

## Step 6: Performance Optimization

### 6.1 Frontend Optimization
```bash
cd frontend

# Analyze bundle size
npm run build
npx vite-bundle-visualizer

# Run Lighthouse audit
npx lighthouse https://foodberg.org --view

# Target scores:
# Performance: 95+
# Accessibility: 100
# Best Practices: 100
# SEO: 100
```

### 6.2 Backend Optimization
- Redis caching: 1-hour TTL for price data
- Connection pooling: Configured in FastAPI
- Rate limiting: 10 req/sec per IP (add middleware)

## Step 7: Post-Deployment Checklist

### Security
- [ ] HTTPS enabled (SSL certificate active)
- [ ] CORS configured correctly
- [ ] API keys in environment variables (not code)
- [ ] Security headers set (Netlify config)
- [ ] Rate limiting enabled

### Performance
- [ ] Lighthouse score 95+
- [ ] API response time <500ms
- [ ] WebSocket latency <100ms
- [ ] First Contentful Paint <1.5s

### Functionality
- [ ] All 6 dashboards load without errors
- [ ] WebSocket connection establishes
- [ ] Recipe calculator works
- [ ] Price data displays correctly
- [ ] Charts render properly
- [ ] Mobile responsive (test on phone/tablet)

### Monitoring
- [ ] Uptime Robot monitoring active
- [ ] Sentry error tracking configured
- [ ] Analytics tracking (optional)
- [ ] Health check endpoints responding

### Documentation
- [ ] README.md updated with production URLs
- [ ] API docs accessible at /docs
- [ ] User guide available
- [ ] Support email configured

## Step 8: Launch Preparation

### 8.1 Beta Testing
1. Recruit 5-10 professional chefs
2. Provide Pro tier access (free for 2 weeks)
3. Collect feedback via Typeform
4. Iterate on critical issues

### 8.2 Marketing Materials
- Landing page with testimonials
- 3-minute demo video (Loom)
- Product screenshots (16 images)
- Press kit (logo, description, founder bio)

### 8.3 Launch Strategy
- **Week 1**: Soft launch to beta users
- **Week 2**: Product Hunt launch (Tuesday)
- **Week 3**: Chef community outreach (Reddit, LinkedIn)
- **Week 4**: Paid ads test ($100 Google Ads)

## Troubleshooting

### Frontend Won't Build
```bash
# Clear cache
rm -rf node_modules frontend/dist
cd frontend
npm install
npm run build
```

### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r backend/requirements.txt

# Test locally
cd backend
python main.py
```

### WebSocket Won't Connect
- Check CORS origins in backend
- Verify frontend ENV has correct backend URL
- Test with ws:// locally, wss:// in production
- Check firewall/security group settings

### Slow Performance
- Enable Redis caching
- Check CDN configuration
- Optimize images
- Enable gzip compression

## Rollback Procedure

### Netlify Rollback
1. Go to Deploys tab
2. Find previous working deploy
3. Click "..." → "Publish deploy"

### Render Rollback
1. Go to Events tab
2. Find previous working deploy
3. Click "Rollback"

## Support

- **Deployment Issues**: https://docs.netlify.com, https://render.com/docs
- **Bug Reports**: https://github.com/foodberg/foodberg/issues
- **Email**: support@foodberg.org

---

**Deployment Time: ~30 minutes**  
**Cost: $0/month (FREE tiers)**  
**Scalability: Handles 1000+ users before needing paid plans**

---

*Last updated: October 13, 2025*

