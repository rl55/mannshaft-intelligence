# ADK API Server Migration Guide

## Overview

Migrating from custom FastAPI application to ADK API Server while maintaining existing functionality.

## Current Architecture

```
Custom FastAPI App (api/main.py)
├── /api/v1/analysis/* - Analysis routes
├── /api/v1/sessions/* - Session management
├── /api/v1/cache/* - Cache monitoring
├── /api/v1/monitoring/* - Monitoring endpoints
├── /api/v1/hitl/* - HITL endpoints
└── WebSocket support for real-time updates
```

## ADK API Server Architecture

```
ADK API Server (adk api_server)
├── Discovers app from adk_app.py
├── Provides standard ADK endpoints
├── Supports custom routes via FastAPI integration
└── WebSocket support via ADK bidi-streaming
```

## Migration Strategy

### Option 1: Hybrid Approach (Recommended)
- Use ADK API Server for agent execution
- Keep custom FastAPI routes for monitoring/HITL/cache
- Integrate both using FastAPI mounting

### Option 2: Full Migration
- Migrate all routes to ADK API Server
- Use ADK's built-in endpoints where possible
- Adapt custom routes to ADK patterns

## Implementation Steps

1. **Create ADK App** ✅
   - Created `adk_app.py` with App and ContextCacheConfig
   - Exports `app` and `root_agent` for ADK discovery

2. **Test ADK API Server**
   ```bash
   cd backend
   adk api_server
   ```

3. **Integrate Custom Routes**
   - Use `get_fast_api_app()` to get ADK's FastAPI app
   - Mount custom routes on the ADK app
   - Maintain WebSocket support

4. **Update Frontend**
   - Update API endpoints if needed
   - Ensure WebSocket connections work with ADK server

## Files Created

- `backend/adk_app.py` - ADK App with context caching

## Next Steps

1. Test ADK API Server locally
2. Integrate custom routes with ADK FastAPI app
3. Test WebSocket functionality
4. Update deployment configuration

