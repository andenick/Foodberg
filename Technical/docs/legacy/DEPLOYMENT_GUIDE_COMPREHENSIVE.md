# Foodberg - Comprehensive Deployment Guide

**Version**: 1.0
**Last Updated**: October 23, 2025
**Database**: 148,559 records (199 MB)

## Table of Contents

- [Quick Start with Docker](#quick-start-with-docker)
- [Local Development](#local-development)
- [Deployment Platforms](#deployment-platforms)
  - [Railway](#railway-deployment)
  - [Render](#render-deployment)
  - [AWS](#aws-deployment)
  - [Vercel + Railway](#vercel--railway)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Production Checklist](#production-checklist)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)

## Quick Start with Docker

### Prerequisites
- Docker Desktop installed
- Git installed
- 500 MB available disk space

### One-Command Deployment

```bash
# Clone repository (if applicable)
cd 

# Start full stack
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Access:**
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Health: http://localhost:8000/health

### Stop Services

```bash
docker-compose down

# Stop and remove volumes (clean restart)
docker-compose down -v
```

## Local Development

### Backend Setup

```bash
cd 

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migration
python database/migrate.py

# Import data (optional - database already populated)
python -m database.import_all_wasde
python -m database.importers.fred_client

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Access**: http://localhost:8000

### Frontend Setup

```bash
cd 

# Install dependencies
npm install

# Start development server
npm run dev
```

**Access**: http://localhost:5173

## Deployment Platforms

### Railway Deployment

Railway provides easy deployment for full-stack applications with automatic SSL and custom domains.

#### Option 1: Full Stack on Railway

**Step 1: Prepare Project**

Create `railway.json` in project root:

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.backend"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

**Step 2: Deploy Backend**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy backend
cd backend
railway up
```

**Step 3: Configure Environment Variables**

In Railway dashboard:
- `DATABASE_PATH=/app/data/foodberg.db`
- `CORS_ORIGINS=https://your-frontend-url.railway.app`
- `PORT=8000`

**Step 4: Add Volume for Database**

In Railway dashboard:
- Add a volume at `/app/data`
- This ensures database persistence across deployments

**Step 5: Deploy Frontend**

Create new Railway service:
- Select "Frontend" folder
- Set build command: `npm run build`
- Set start command: `npx serve -s dist -l $PORT`
- Add environment variable: `VITE_API_BASE_URL=https://your-backend-url.railway.app`

**Cost Estimate**: $5-20/month depending on usage

#### Option 2: Backend Only on Railway

Deploy backend on Railway, host frontend on Vercel (free):

**Backend on Railway:**
- Follow steps 1-4 above
- Set CORS to allow Vercel domain

**Frontend on Vercel:**
- See [Vercel + Railway](#vercel--railway) section below

### Render Deployment

Render offers similar ease with good free tier.

#### Backend Deployment

**Step 1: Create `render.yaml`**

```yaml
services:
  - type: web
    name: foodberg-api
    env: python
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT"
    healthCheckPath: /health
    envVars:
      - key: DATABASE_PATH
        value: /var/data/foodberg.db
      - key: PYTHONUNBUFFERED
        value: 1
    disk:
      name: foodberg-data
      mountPath: /var/data
      sizeGB: 1
```

**Step 2: Deploy via Render Dashboard**

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your Git repository
4. Render auto-detects `render.yaml`
5. Click "Create Web Service"

**Step 3: Add Environment Variables**

In Render dashboard:
- `DATABASE_PATH=/var/data/foodberg.db`
- `CORS_ORIGINS=https://your-frontend.onrender.com`

**Step 4: Upload Database**

```bash
# SSH into Render instance
render ssh foodberg-api

# Upload database (use SCP or manual upload in dashboard)
```

#### Frontend Deployment

**Option 1: Static Site on Render**

```yaml
services:
  - type: web
    name: foodberg-frontend
    env: static
    buildCommand: "cd frontend && npm install && npm run build"
    staticPublishPath: frontend/dist
    routes:
      - type: rewrite
        source: /api/*
        destination: https://foodberg-api.onrender.com/api/*
```

**Option 2: Use Vercel** (recommended for frontend)

**Cost Estimate**: Free tier available, $7/month for starter

### AWS Deployment

Comprehensive AWS deployment using ECS, RDS, and S3.

#### Architecture

```
Route 53 (DNS)
    ↓
CloudFront (CDN)
    ↓
S3 (Frontend) + ALB (API Load Balancer)
                    ↓
                ECS Fargate (Backend Containers)
                    ↓
                RDS or EFS (Database)
```

#### Step 1: Setup AWS CLI

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
```

#### Step 2: Create ECR Repositories

```bash
# Create repository for backend
aws ecr create-repository --repository-name foodberg-backend

# Create repository for frontend (if using ECS for both)
aws ecr create-repository --repository-name foodberg-frontend
```

#### Step 3: Build and Push Docker Images

```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build backend
docker build -f Dockerfile.backend -t foodberg-backend .

# Tag and push
docker tag foodberg-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/foodberg-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/foodberg-backend:latest

# Build frontend
docker build -f Dockerfile.frontend -t foodberg-frontend .
docker tag foodberg-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/foodberg-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/foodberg-frontend:latest
```

#### Step 4: Create ECS Cluster

```bash
# Create cluster
aws ecs create-cluster --cluster-name foodberg-cluster

# Create task definition (see task-definition.json below)
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster foodberg-cluster \
  --service-name foodberg-backend \
  --task-definition foodberg-backend:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

**task-definition.json**:
```json
{
  "family": "foodberg-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/foodberg-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_PATH",
          "value": "/app/data/foodberg.db"
        }
      ],
      "mountPoints": [
        {
          "sourceVolume": "foodberg-data",
          "containerPath": "/app/data"
        }
      ]
    }
  ],
  "volumes": [
    {
      "name": "foodberg-data",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-xxxxx"
      }
    }
  ]
}
```

#### Step 5: Setup EFS for Database Persistence

```bash
# Create EFS file system
aws efs create-file-system --creation-token foodberg-data

# Create mount target
aws efs create-mount-target \
  --file-system-id fs-xxxxx \
  --subnet-id subnet-xxxxx \
  --security-groups sg-xxxxx
```

#### Step 6: Deploy Frontend to S3 + CloudFront

```bash
# Build frontend
cd frontend
npm run build

# Create S3 bucket
aws s3 mb s3://foodberg-frontend

# Upload files
aws s3 sync dist/ s3://foodberg-frontend --acl public-read

# Create CloudFront distribution (via console or CLI)
# Point to S3 bucket
# Add custom domain if desired
```

**Cost Estimate**: $20-100/month depending on traffic

### Vercel + Railway

Optimal setup: Free frontend on Vercel, backend on Railway.

#### Backend on Railway

Follow [Railway Backend steps](#option-2-backend-only-on-railway)

#### Frontend on Vercel

**Step 1: Install Vercel CLI**

```bash
npm install -g vercel
```

**Step 2: Configure Frontend**

Create `frontend/.env.production`:
```
VITE_API_BASE_URL=https://your-backend.railway.app
```

**Step 3: Deploy**

```bash
cd frontend

# Login to Vercel
vercel login

# Deploy
vercel --prod
```

**Step 4: Configure Environment Variables in Vercel Dashboard**

- `VITE_API_BASE_URL`: Your Railway backend URL

**Step 5: Setup Custom Domain (Optional)**

In Vercel dashboard:
1. Go to Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed

**Cost**: Free for frontend, $5-20/month for backend

## Environment Configuration

### Development (.env.development)

```env
NODE_ENV=development
DATABASE_PATH=./backend/data/foodberg.db
API_HOST=localhost
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
VITE_API_BASE_URL=http://localhost:8000
LOG_LEVEL=DEBUG
```

### Staging (.env.staging)

```env
NODE_ENV=staging
DATABASE_PATH=/app/data/foodberg.db
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://staging.yourdomain.com
VITE_API_BASE_URL=https://api-staging.yourdomain.com
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=120
```

### Production (.env.production)

```env
NODE_ENV=production
DATABASE_PATH=/app/data/foodberg.db
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
VITE_API_BASE_URL=https://api.yourdomain.com
LOG_LEVEL=WARNING
RATE_LIMIT_PER_MINUTE=60
SECRET_KEY=<generate-secure-random-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com
```

**Generate SECRET_KEY:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

## Database Setup

### Option 1: Use Existing Database (Recommended)

The database file (`backend/data/foodberg.db`) contains 148,559 records and can be deployed directly:

```bash
# Copy database to deployment
scp backend/data/foodberg.db user@server:/app/data/

# Or mount as Docker volume
docker run -v ./backend/data:/app/data foodberg-backend
```

### Option 2: Import Fresh Data

```bash
# Run migration
python backend/database/migrate.py

# Import WASDE data
python -m backend.database.import_all_wasde

# Import FRED data
python -m backend.database.importers.fred_client
```

**Time Required**: ~30-60 seconds total

### Database Backup

**Automated Backup Script:**

```bash
#!/bin/bash
# backup_database.sh

DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="/backups"
DB_PATH="/app/data/foodberg.db"

# Create backup
sqlite3 $DB_PATH ".backup '$BACKUP_DIR/foodberg_$DATE.db'"

# Compress
gzip $BACKUP_DIR/foodberg_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -name "foodberg_*.db.gz" -mtime +30 -delete

echo "Backup completed: foodberg_$DATE.db.gz"
```

**Schedule with cron:**
```cron
0 2 * * * /path/to/backup_database.sh
```

## Production Checklist

### Pre-Deployment

- [ ] Environment variables configured
- [ ] Database backed up
- [ ] CORS origins set correctly
- [ ] SECRET_KEY generated and set
- [ ] SSL certificate ready (handled by platform)
- [ ] Custom domain DNS configured
- [ ] Health check endpoint tested
- [ ] API rate limiting configured

### Security

- [ ] HTTPS enforced
- [ ] CORS properly configured
- [ ] Security headers in nginx config
- [ ] API keys stored securely (environment variables)
- [ ] Database file permissions restricted
- [ ] No sensitive data in logs
- [ ] Git secrets not committed

### Performance

- [ ] Gzip compression enabled
- [ ] Static assets cached (1 year)
- [ ] Database indexes verified
- [ ] Health checks configured
- [ ] Auto-restart policy set
- [ ] Resource limits appropriate

### Monitoring

- [ ] Health check endpoint: `/health`
- [ ] Log aggregation configured
- [ ] Error tracking setup (optional: Sentry)
- [ ] Uptime monitoring (optional: UptimeRobot)
- [ ] Database size monitoring

## Monitoring & Maintenance

### Health Checks

**Backend Health Endpoint:**
```bash
curl https://your-api.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "records": 148559
}
```

### Logging

**View Logs (Docker):**
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

**View Logs (Railway):**
```bash
railway logs
```

**View Logs (Render):**
Available in dashboard under "Logs" tab

### Database Maintenance

**Vacuum Database (Optimize Size):**
```bash
sqlite3 /app/data/foodberg.db "VACUUM;"
```

**Check Database Size:**
```bash
du -h /app/data/foodberg.db
```

**Verify Record Count:**
```bash
sqlite3 /app/data/foodberg.db "SELECT COUNT(*) FROM wasde_data;"
sqlite3 /app/data/foodberg.db "SELECT COUNT(*) FROM economic_indicators;"
```

### Updating Data

**Update WASDE Data:**
```bash
# SSH into server or exec into container
docker exec -it foodberg-backend bash

# Run import
python -m database.import_all_wasde
```

**Update FRED Data:**
```bash
python -m database.importers.fred_client
```

## Troubleshooting

### Issue: Port Already in Use

```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (Windows)
taskkill /PID <process_id> /F

# Or start on different port
uvicorn main:app --port 8001
```

### Issue: Database Not Found

```bash
# Check database path
ls -la /app/data/

# Run migration
python database/migrate.py

# Verify permissions
chmod 644 /app/data/foodberg.db
```

### Issue: CORS Errors

Update `CORS_ORIGINS` environment variable:
```bash
# Allow multiple origins
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Issue: Import Script Fails

```bash
# Check Robin data directory exists
ls -la 

# Check API keys
cat  api_keys.json

# Run with verbose logging
python -m database.import_all_wasde --verbose
```

### Issue: Frontend Can't Connect to Backend

1. Check `VITE_API_BASE_URL` environment variable
2. Verify backend is running: `curl https://your-api.com/health`
3. Check CORS configuration in backend
4. Check browser console for errors

### Issue: Docker Build Fails

```bash
# Check Docker is running
docker ps

# Rebuild without cache
docker-compose build --no-cache

# Check logs
docker-compose logs
```

## Platform-Specific Notes

### Railway
- Automatic SSL
- Automatic deployments from Git
- Built-in metrics dashboard
- Volume persistence available
- Custom domains supported

### Render
- Free tier available
- Automatic SSL
- Git-based deployments
- Persistent disks
- Health checks included

### AWS
- Most control and scalability
- Higher complexity
- Pay-per-use pricing
- Full infrastructure control
- Requires more DevOps knowledge

### Vercel
- Best for frontend only
- Excellent performance (CDN)
- Free tier generous
- Automatic deployments
- Serverless functions available

## Cost Comparison

| Platform | Frontend | Backend | Database | Total/Month | Free Tier |
|----------|----------|---------|----------|-------------|-----------|
| Railway | $5-10 | $10-20 | Included | $15-30 | $5 credit |
| Render | $7 | $7-25 | $7 | $14-39 | Free tier |
| AWS | $1-5 | $15-50 | $10-30 | $26-85 | 12 months |
| Vercel+Railway | Free | $10-20 | Included | $10-20 | Frontend free |

**Recommended for Start**: Vercel (frontend) + Railway (backend) = $10-20/month

## Support & Resources

**Documentation:**
- API Documentation: `backend/API_DOCUMENTATION.md`
- Database Technical Docs: `backend/database/README.md`
- User Guide: `USER_GUIDE_PRICE_DATABASE.md`
- Data Status: `DATA_STATUS.md`

**External Resources:**
- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs
- AWS ECS Guide: https://aws.amazon.com/ecs/getting-started
- Vercel Docs: https://vercel.com/docs
- Docker Docs: https://docs.docker.com

---

**Version**: 1.0
**Last Updated**: October 23, 2025
**Project**: Foodberg Price Database
**Repository**: 
