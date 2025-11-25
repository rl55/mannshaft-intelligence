# Deployment Guide: GCP Cloud Run & Vertex AI

## Overview

This guide covers deploying the **Mannshaft Intelligence SaaS BI Agent Platform** to Google Cloud Platform using **Google Agent Development Kit (ADK)**.

**Deployment Status**: ✅ **Ready for Cloud Run** | ✅ **Ready for Vertex AI**

---

## Prerequisites

- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed (for local builds)
- ADK-enabled codebase (migrated from legacy Gemini implementation)

---

## Architecture Overview

### ADK-Based Architecture

```
Frontend (Next.js)
    ↓ HTTP/WebSocket
ADK API Server (FastAPI + ADK)
    ↓
ADK SequentialAgent (Main Orchestrator)
    ├── ParallelAgent (Analytical Coordinator)
    │   ├── RevenueAgent (LlmAgent)
    │   ├── ProductAgent (LlmAgent)
    │   └── SupportAgent (LlmAgent)
    ├── SynthesizerAgent (LlmAgent with tools)
    ├── GovernanceAgent (BaseAgent)
    └── EvaluationAgent (LlmAgent)
    ↓
Google Cloud Services:
    - Cloud SQL (PostgreSQL) - Session & Cache Storage
    - Secret Manager - API Keys & Credentials
    - Cloud Storage - Optional file storage
    - Vertex AI - Optional LLM endpoint
```

---

## Option 1: Deploy to Google Cloud Run

### Why Cloud Run?

✅ **Serverless**: No infrastructure management  
✅ **Auto-scaling**: Handles traffic spikes automatically  
✅ **Pay-per-use**: Only pay for actual execution time  
✅ **ADK Compatible**: Fully supports ADK API Server  
✅ **WebSocket Support**: Real-time updates work out of the box  

### Step 1: Prepare Backend

#### 1.1 Create Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run ADK unified API server
CMD exec uvicorn adk_unified_main:app --host 0.0.0.0 --port $PORT
```

#### 1.2 Update Environment Variables

Create `backend/.env.production`:

```bash
# Google Cloud Configuration
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# Database (Cloud SQL)
DATABASE_URL=postgresql://user:password@/dbname?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME

# Secrets (loaded from Secret Manager)
GEMINI_API_KEY=  # Will be loaded from Secret Manager
GOOGLE_CREDENTIALS_PATH=/secrets/google-credentials.json

# Google Sheets IDs
REVENUE_SHEET_ID=your-revenue-sheet-id
PRODUCT_SHEET_ID=your-product-sheet-id
SUPPORT_SHEET_ID=your-support-sheet-id

# API Configuration
API_HOST=0.0.0.0
API_PORT=8080
CORS_ORIGINS=https://your-frontend-domain.com

# ADK Configuration
ADK_APP_NAME=saas_bi_agent_adk
```

### Step 2: Set Up Cloud SQL

```bash
# Create Cloud SQL PostgreSQL instance
gcloud sql instances create saas-bi-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=YOUR_ROOT_PASSWORD

# Create database
gcloud sql databases create agent_cache --instance=saas-bi-db

# Create user
gcloud sql users create agent_user \
    --instance=saas-bi-db \
    --password=YOUR_USER_PASSWORD
```

### Step 3: Store Secrets in Secret Manager

```bash
# Store Gemini API key
echo -n "your-gemini-api-key" | gcloud secrets create gemini-api-key --data-file=-

# Store Google credentials JSON
gcloud secrets create google-credentials --data-file=path/to/service-account.json

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 4: Build and Deploy

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build container image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/saas-bi-backend:latest

# Deploy to Cloud Run
gcloud run deploy saas-bi-backend \
    --image gcr.io/YOUR_PROJECT_ID/saas-bi-backend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "DATABASE_URL=postgresql://user:pass@/dbname?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME" \
    --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,GOOGLE_CREDENTIALS=google-credentials:latest" \
    --add-cloudsql-instances PROJECT_ID:REGION:INSTANCE_NAME \
    --memory 4Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 1 \
    --service-account YOUR_SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com
```

### Step 5: Deploy Frontend

#### Option A: Vercel (Recommended)

```bash
cd frontend
vercel deploy --prod

# Set environment variables in Vercel dashboard:
# NEXT_PUBLIC_API_URL=https://saas-bi-backend-xxx.run.app
# NEXT_PUBLIC_WS_URL=wss://saas-bi-backend-xxx.run.app
```

#### Option B: Cloud Run

```bash
# Build frontend
cd frontend
npm run build

# Create Dockerfile
cat > Dockerfile << EOF
FROM node:20-alpine
WORKDIR /app
COPY .next ./.next
COPY public ./public
COPY package*.json ./
RUN npm ci --only=production
EXPOSE 3000
CMD ["npm", "start"]
EOF

# Deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/saas-bi-frontend:latest
gcloud run deploy saas-bi-frontend \
    --image gcr.io/YOUR_PROJECT_ID/saas-bi-frontend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "NEXT_PUBLIC_API_URL=https://saas-bi-backend-xxx.run.app" \
    --memory 512Mi \
    --cpu 1
```

---

## Option 2: Deploy to Vertex AI

### Why Vertex AI?

✅ **Managed ADK Runtime**: Google-managed ADK execution environment  
✅ **Enterprise Scale**: Handles high-volume workloads  
✅ **Integrated Monitoring**: Built-in observability  
✅ **Cost Optimization**: Optimized for AI workloads  

### Step 1: Prepare ADK App

Ensure `backend/adk_app.py` is properly configured:

```python
from google.adk.apps.app import App
from google.adk.agents.context_cache_config import ContextCacheConfig
from adk_agents.orchestrator import create_main_orchestrator

root_agent = create_main_orchestrator()
context_cache_config = ContextCacheConfig()

app = App(
    name="saas_bi_agent_adk",
    root_agent=root_agent,
    context_cache_config=context_cache_config
)
```

### Step 2: Deploy to Vertex AI Agent Engine

```bash
# Install Vertex AI CLI
pip install google-cloud-aiplatform

# Deploy ADK app
gcloud ai agents deploy \
    --app-path=backend/adk_app.py \
    --region=us-central1 \
    --project=YOUR_PROJECT_ID \
    --display-name="SaaS BI Agent" \
    --description="Multi-agent SaaS BI analysis platform"
```

### Step 3: Configure Endpoints

```bash
# Create endpoint
gcloud ai endpoints create \
    --region=us-central1 \
    --display-name="SaaS BI Agent Endpoint"

# Deploy model to endpoint
gcloud ai endpoints deploy-model ENDPOINT_ID \
    --model=MODEL_ID \
    --region=us-central1
```

---

## Configuration Reference

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Gemini API key | `AIza...` |
| `DATABASE_URL` | Cloud SQL connection string | `postgresql://...` |
| `REVENUE_SHEET_ID` | Google Sheets Revenue ID | `1abc...` |
| `PRODUCT_SHEET_ID` | Google Sheets Product ID | `1def...` |
| `SUPPORT_SHEET_ID` | Google Sheets Support ID | `1ghi...` |
| `GOOGLE_CREDENTIALS_PATH` | Service account JSON path | `/secrets/...` |

### Cloud Run Resource Requirements

| Resource | Recommended | Minimum |
|----------|-------------|---------|
| **CPU** | 2 vCPU | 1 vCPU |
| **Memory** | 4 GB | 2 GB |
| **Timeout** | 300s | 60s |
| **Max Instances** | 10 | 1 |
| **Min Instances** | 1 | 0 |

---

## Health Checks

### Backend Health Endpoint

```bash
curl https://your-backend.run.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "cache": "connected",
  "adk_app": "saas_bi_agent_adk"
}
```

### ADK API Endpoints

- `/adk/agents` - List available agents
- `/adk/sessions` - Session management
- `/api/v1/analysis` - Analysis endpoints
- `/api/v1/sessions` - Session endpoints
- `/api/v1/monitoring` - Monitoring endpoints
- `/api/v1/hitl` - HITL endpoints

---

## Monitoring & Logging

### Cloud Run Logs

```bash
# View logs
gcloud run services logs read saas-bi-backend --region us-central1

# Stream logs
gcloud run services logs tail saas-bi-backend --region us-central1
```

### Cloud Monitoring

- **Metrics**: Request count, latency, error rate
- **Traces**: Distributed tracing for multi-agent workflows
- **Alerts**: Set up alerts for errors, latency spikes

---

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify Cloud SQL instance is running
   - Check connection string format
   - Ensure Cloud Run has Cloud SQL connection permission

2. **Secrets Not Loading**
   - Verify service account has `secretmanager.secretAccessor` role
   - Check secret names match exactly
   - Ensure secrets exist in Secret Manager

3. **ADK Agent Not Found**
   - Verify `adk_app.py` exports `app` and `root_agent`
   - Check ADK version compatibility
   - Review logs for import errors

4. **WebSocket Connection Failed**
   - Cloud Run supports WebSockets ✅
   - Check CORS configuration
   - Verify frontend WebSocket URL is correct

---

## Cost Estimation

### Cloud Run (Monthly)

- **Compute**: ~$50-100/month (2 vCPU, 4GB, 1 min instance)
- **Cloud SQL**: ~$10-30/month (db-f1-micro)
- **Networking**: ~$5-10/month
- **Total**: ~$65-140/month

### Vertex AI (Monthly)

- **Agent Engine**: ~$100-200/month (based on usage)
- **Cloud SQL**: ~$10-30/month
- **Total**: ~$110-230/month

---

## Next Steps

1. ✅ Deploy backend to Cloud Run
2. ✅ Deploy frontend to Vercel/Cloud Run
3. ✅ Configure monitoring and alerts
4. ✅ Set up CI/CD pipeline
5. ✅ Load testing and optimization

---

## Additional Resources

- [ADK Documentation](https://google.github.io/adk-docs/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)

---

## Support

For deployment issues, check:
1. Cloud Run logs
2. ADK agent logs
3. Database connection status
4. Secret Manager access

