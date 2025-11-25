"""
ADK API Server Integration
Note: ADK API Server can be run directly using `adk api_server` command.
This file maintains custom routes for monitoring, HITL, and cache management.

To use ADK API Server:
1. Run: `cd backend && adk api_server`
2. ADK will automatically discover `app` from `adk_app.py`
3. Agent execution endpoints will be available via ADK API Server

For custom routes (monitoring, HITL, cache), continue using this FastAPI app
or integrate them separately as needed.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from utils.config import config
from utils.logger import logger
from cache.cache_manager import CacheManager

# Import custom routes
from api.routes import sessions, cache, monitoring, hitl


# Global cache manager instance
cache_manager: CacheManager = None


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Application lifespan manager."""
    global cache_manager
    
    # Startup
    logger.info("Starting custom API routes (monitoring, HITL, cache)")
    cache_manager = CacheManager(
        db_path=config.get('database.path', 'data/agent_cache.db'),
        schema_path=config.get('database.schema_path', 'data/schema.sql')
    )
    logger.info("Cache manager initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down custom API routes")
    if cache_manager:
        cache_manager.close()


# Create FastAPI app for custom routes
app = FastAPI(
    title=config.get('app.name', 'SaaS BI Agent Custom Routes'),
    version=config.get('app.version', '1.0.0'),
    description="Custom routes for monitoring, HITL, and cache management",
    lifespan=lifespan
)

# CORS middleware
cors_origins = config.get('api.cors_origins', ['*'])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include custom routes
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
app.include_router(cache.router, prefix="/api/v1/cache", tags=["Cache"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])
app.include_router(hitl.router, prefix="/api/v1/hitl", tags=["HITL"])

# Note: Agent execution is handled by ADK API Server
# Run ADK API Server separately: `adk api_server`


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": config.get('app.name', 'SaaS BI Agent Custom Routes'),
        "version": config.get('app.version', '1.0.0'),
        "status": "running",
        "note": "Agent execution handled by ADK API Server. Run 'adk api_server' separately."
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "cache": "connected" if cache_manager else "disconnected"
    }


if __name__ == "__main__":
    import uvicorn
    
    api_config = {
        'host': config.get('api.host', '0.0.0.0'),
        'port': config.get('api.port', 8001),  # Different port from ADK API Server
        'reload': config.get('api.reload', False)
    }
    
    uvicorn.run(
        "adk_api_main:app",
        host=api_config.get('host', '0.0.0.0'),
        port=api_config.get('port', 8001),
        reload=api_config.get('reload', False)
    )

