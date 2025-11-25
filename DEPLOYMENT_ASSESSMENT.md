# Deployment Assessment: Google Cloud Run

## Executive Summary

**Current Status**: ✅ **Deployable with modifications**

The codebase is well-structured and can be deployed to Google Cloud Run, but requires several changes for production readiness, primarily around database persistence and environment configuration.

---

## ✅ What Works Well

1. **FastAPI Backend**: Fully compatible with Cloud Run
   - Uses standard ASGI (Uvicorn)
   - Stateless API design
   - WebSocket support (Cloud Run supports WebSockets)

2. **Next.js Frontend**: Can be deployed separately
   - Static export possible
   - Or deploy as separate Cloud Run service

3. **Environment Variables**: Already using `python-dotenv` and config system
   - Easy to migrate to Cloud Run environment variables

4. **Google Services Integration**: Already using Google APIs
   - Gemini API ✅
   - Google Sheets API ✅
   - Can use Workload Identity for authentication

---

## ⚠️ Critical Changes Required

### 1. **Database Persistence** (HIGH PRIORITY)

**Current Issue**: SQLite files stored in `data/` directory
- SQLite files are ephemeral in Cloud Run containers
- Data will be lost on container restart/redeploy

**Solutions**:

#### Option A: Cloud SQL (Recommended for Production)
```python
# Replace SQLite with PostgreSQL/MySQL via Cloud SQL
# Use SQLAlchemy with Cloud SQL Proxy or Unix socket
DATABASE_URL = os.getenv('DATABASE_URL')  # Cloud SQL connection string
```

**Required Changes**:
- Replace `sqlite3` with `sqlalchemy` + `psycopg2` or `pymysql`
- Update `CacheManager` and `DatabaseManager` to use SQLAlchemy
- Configure Cloud SQL instance
- Use Cloud SQL Proxy or Unix socket connection

#### Option B: Cloud Storage (For Development/Testing)
- Mount Cloud Storage bucket as volume (not recommended for production)
- Use Cloud Storage for SQLite file persistence

#### Option C: Cloud Firestore (NoSQL Alternative)
- Migrate schema to Firestore
- More significant refactoring required

**Recommendation**: **Option A (Cloud SQL PostgreSQL)**

---

### 2. **Environment Variables & Secrets**

**Current**: Using `.env` files and `config.yaml`

**Required Changes**:
- Move all secrets to Google Secret Manager
- Use Cloud Run environment variables for non-sensitive config
- Update `config.yaml` to read from environment variables only

**Secrets to Migrate**:
- `GEMINI_API_KEY` → Secret Manager
- `GOOGLE_CREDENTIALS_PATH` → Secret Manager (or use Workload Identity)
- `REVENUE_SHEET_ID`, `PRODUCT_SHEET_ID`, `SUPPORT_SHEET_ID` → Environment variables
- Database credentials → Secret Manager

---

### 3. **File System Paths**

**Current**: Hardcoded paths like `data/agent_cache.db`, `data/schema.sql`

**Required Changes**:
```python
# Use environment variables or Cloud Storage
DB_PATH = os.getenv('DB_PATH', '/tmp/agent_cache.db')  # Temporary for Cloud Run
# Or use Cloud SQL connection string
```

---

### 4. **CORS Configuration**

**Current**: `cors_origins: ["*"]` in `config.yaml`

**Required Changes**:
```python
# In main.py
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')
# Set to your frontend domain(s)
```

---

### 5. **Health Checks**

**Current**: No health check endpoint

**Required Addition**:
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

---

### 6. **Logging**

**Current**: File-based logging (`logs/app.log`)

**Required Changes**:
- Use Cloud Logging (stdout/stderr)
- Cloud Run automatically captures stdout/stderr
- Remove file-based logging or use Cloud Storage

---

### 7. **Frontend API URLs**

**Current**: Hardcoded `localhost:8000` in several places

**Required Changes**:
- Ensure all API calls use `process.env.NEXT_PUBLIC_API_URL`
- Set environment variable in Cloud Run/deployment config

---

## 📋 Deployment Checklist

### Backend (Cloud Run)

- [ ] Create Dockerfile for FastAPI backend
- [ ] Replace SQLite with Cloud SQL PostgreSQL
- [ ] Migrate secrets to Secret Manager
- [ ] Update environment variable configuration
- [ ] Add health check endpoint
- [ ] Configure Cloud Run service:
  - CPU: 2+ vCPU (for agent processing)
  - Memory: 4GB+ (for LLM operations)
  - Timeout: 300s+ (for long-running analyses)
  - Max instances: Based on load
  - Min instances: 1 (for cold start reduction)
- [ ] Configure Cloud SQL instance
- [ ] Set up Cloud IAM for service account
- [ ] Configure CORS for frontend domain
- [ ] Test WebSocket connections

### Frontend (Vercel/Cloud Run/Cloud Storage)

**Option 1: Vercel (Recommended)**
- [ ] Deploy Next.js to Vercel
- [ ] Set environment variables:
  - `NEXT_PUBLIC_API_URL=https://your-backend.run.app`
  - `NEXT_PUBLIC_WS_URL=wss://your-backend.run.app`
- [ ] Configure custom domain

**Option 2: Cloud Run**
- [ ] Create Dockerfile for Next.js
- [ ] Build static export or run Node.js server
- [ ] Deploy to Cloud Run
- [ ] Configure environment variables

**Option 3: Cloud Storage + Cloud CDN**
- [ ] Export Next.js as static site
- [ ] Upload to Cloud Storage bucket
- [ ] Configure Cloud CDN
- [ ] Set up custom domain

---

## 🐳 Dockerfile Examples

### Backend Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run application
CMD exec uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### Frontend Dockerfile (if deploying to Cloud Run)

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
RUN npm ci --only=production

EXPOSE 3000
CMD ["npm", "start"]
```

---

## 🔧 Required Code Changes Summary

### 1. Database Migration (Highest Priority)

**File**: `backend/cache/cache_manager.py`, `backend/database/db_manager.py`

```python
# Replace SQLite with SQLAlchemy + PostgreSQL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL')  # Cloud SQL connection string
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
```

### 2. Environment Configuration

**File**: `backend/utils/config.py`

```python
# Ensure all config reads from environment variables
# Use Secret Manager client for secrets
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

### 3. Health Check Endpoint

**File**: `backend/api/main.py`

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": config.get('app.version', '1.0.0'),
        "database": "connected" if check_db_connection() else "disconnected"
    }
```

### 4. CORS Update

**File**: `backend/api/main.py`

```python
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Resource Requirements

### Cloud Run Service Configuration

```yaml
Backend Service:
  CPU: 2 vCPU
  Memory: 4GB
  Timeout: 300s
  Max Instances: 10
  Min Instances: 1
  Concurrency: 80
  
Frontend Service (if using Cloud Run):
  CPU: 1 vCPU
  Memory: 512MB
  Timeout: 60s
  Max Instances: 10
  Min Instances: 0
```

### Cloud SQL Instance

```yaml
Database:
  Type: PostgreSQL 15
  Tier: db-f1-micro (dev) or db-n1-standard-1 (prod)
  Storage: 10GB (auto-grow enabled)
  Backup: Enabled (7-day retention)
  High Availability: Recommended for production
```

---

## 🚀 Deployment Steps

### 1. Prepare Backend

```bash
# Build and push Docker image
gcloud builds submit --tag gcr.io/PROJECT_ID/saas-bi-backend

# Deploy to Cloud Run
gcloud run deploy saas-bi-backend \
  --image gcr.io/PROJECT_ID/saas-bi-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=$(gcloud secrets versions access latest --secret=gemini-api-key)" \
  --set-env-vars "DATABASE_URL=$(gcloud secrets versions access latest --secret=database-url)" \
  --set-env-vars "CORS_ORIGINS=https://your-frontend-domain.com" \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 1
```

### 2. Prepare Frontend

```bash
# Build Next.js app
cd frontend
npm run build

# Deploy to Vercel (recommended)
vercel deploy --prod

# Or deploy to Cloud Run
gcloud builds submit --tag gcr.io/PROJECT_ID/saas-bi-frontend
gcloud run deploy saas-bi-frontend \
  --image gcr.io/PROJECT_ID/saas-bi-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "NEXT_PUBLIC_API_URL=https://saas-bi-backend-xxx.run.app" \
  --set-env-vars "NEXT_PUBLIC_WS_URL=wss://saas-bi-backend-xxx.run.app"
```

---

## ⚡ Quick Wins (Can Deploy Now)

If you want to deploy quickly for testing:

1. **Use Cloud SQL Proxy with SQLite** (temporary)
   - Mount Cloud Storage bucket
   - Store SQLite file in bucket
   - Not recommended for production

2. **Deploy Frontend to Vercel** (easiest)
   - Minimal changes needed
   - Just update API URLs

3. **Deploy Backend with SQLite in /tmp**
   - Accept data loss on restart
   - Good for testing only

---

## 🎯 Recommended Deployment Strategy

### Phase 1: Quick Test Deployment
1. Deploy frontend to Vercel
2. Deploy backend to Cloud Run with SQLite (temporary)
3. Test end-to-end flow

### Phase 2: Production Readiness
1. Set up Cloud SQL PostgreSQL
2. Migrate database code to SQLAlchemy
3. Move secrets to Secret Manager
4. Configure proper CORS
5. Add health checks
6. Set up monitoring and alerts

### Phase 3: Optimization
1. Enable Cloud CDN for frontend
2. Configure auto-scaling
3. Set up CI/CD pipeline
4. Add monitoring dashboards
5. Implement backup strategy

---

## 📝 Additional Considerations

1. **WebSocket Support**: Cloud Run supports WebSockets ✅
2. **Cold Starts**: Consider min-instances=1 to reduce latency
3. **Cost Optimization**: Use Cloud SQL Serverless for dev/test
4. **Monitoring**: Integrate with Cloud Monitoring and Cloud Trace
5. **Security**: Use Workload Identity instead of service account keys
6. **CI/CD**: Set up Cloud Build triggers for automated deployments

---

## ✅ Conclusion

**Deployment Readiness**: **75%**

The codebase is well-structured and can be deployed to Cloud Run with the following priority changes:

1. **Must Fix**: Database persistence (SQLite → Cloud SQL)
2. **Should Fix**: Secrets management, CORS, health checks
3. **Nice to Have**: Monitoring, CI/CD, optimization

**Estimated Time to Production-Ready**: 2-3 days of development work

**Recommended Approach**: Start with a test deployment using temporary solutions, then migrate to production-ready infrastructure.

