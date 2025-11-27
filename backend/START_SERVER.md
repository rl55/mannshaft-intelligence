# Starting the ADK Unified Server

## Problem
When running `uvicorn` directly, it may use system Python instead of venv Python, causing `ModuleNotFoundError: No module named 'google.adk'`.

## ✅ Solution: Use venv's Python

### Option 1: Use Python module syntax (Recommended)
```bash
cd backend
source venv/bin/activate
python3 -m uvicorn adk_unified_main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 2: Use convenience script
```bash
cd backend
./run_adk_server.sh
```

### Option 3: Use direct Python execution
```bash
cd backend
source venv/bin/activate
python3 adk_unified_main.py
```

## ❌ Don't Use
```bash
# This may use system Python instead of venv Python
uvicorn adk_unified_main:app --host 0.0.0.0 --port 8000 --reload
```

## Verification
After starting, verify the server is running:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "cache": "connected",
  "adk_app": "saas_bi_agent_adk"
}
```

