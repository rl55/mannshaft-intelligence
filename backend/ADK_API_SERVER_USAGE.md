# ADK API Server Usage Guide

## Problem

When running `adk api_server`, the ADK API Server starts but doesn't include our custom routes (`/api/v1/analysis/trigger`, WebSocket endpoints, etc.), causing 404 errors from the frontend.

**Error seen:**
```
INFO:     127.0.0.1:53592 - "OPTIONS /api/v1/analysis/trigger HTTP/1.1" 404 Not Found
INFO:     "WebSocket /api/v1/analysis/{session_id}/ws" 403
```

## Solution

**DO NOT use `adk api_server` command directly.** Instead, use `adk_unified_main.py` which combines ADK API Server with our custom routes.

## Running the Server

### ✅ Recommended: Use Unified App (with venv activated)
```bash
cd backend
source venv/bin/activate  # IMPORTANT: Activate venv first!
python adk_unified_main.py
# OR use the convenience script:
./run_adk_server.sh
# OR with uvicorn (venv must be activated):
uvicorn adk_unified_main:app --host 0.0.0.0 --port 8000 --reload
```

**Important:** Always activate the venv first! ADK is installed in the venv, not system Python.

### ⚠️ Alternative: Use Original FastAPI App (temporary)
If you need to use the original app while migrating:
```bash
cd backend
python api/main.py
# OR
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### ❌ Do NOT use:
```bash
adk api_server  # This will NOT include custom routes!
```

## What's Included

The unified app includes:
- ✅ ADK API Server routes (agent execution via ADK)
- ✅ Custom analysis routes (`/api/v1/analysis/*`)
- ✅ Custom session routes (`/api/v1/sessions/*`)
- ✅ Custom cache routes (`/api/v1/cache/*`)
- ✅ Custom monitoring routes (`/api/v1/monitoring/*`)
- ✅ Custom HITL routes (`/api/v1/hitl/*`)
- ✅ WebSocket support for real-time updates

## Architecture

```
adk_unified_main.py
├── Uses get_fast_api_app() to get ADK's FastAPI app
├── Adds custom routes via lifespan hook
└── Combines both into unified app
```

## Next Steps

1. Test the unified app: `python adk_unified_main.py`
2. Verify all routes are accessible
3. Test WebSocket connections
4. Update deployment to use unified app

