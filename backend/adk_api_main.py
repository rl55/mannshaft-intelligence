"""
ADK API Server Integration
Integrates ADK API Server with custom FastAPI routes for monitoring, HITL, and cache management.

This file creates a FastAPI app that combines:
- ADK API Server endpoints (agent execution)
- Custom routes (monitoring, HITL, cache, sessions)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from google.adk.runtime.web import get_fast_api_app
from adk_app import app as adk_app
from utils.config import config
from utils.logger import logger
from cache.cache_manager import CacheManager

# Import custom routes
from api.routes import sessions, cache, monitoring, hitl


# Global cache manager instance (for custom routes that still need it)
cache_manager: CacheManager = None


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Application lifespan manager."""
    global cache_manager
    
    # Startup
    logger.info("Starting ADK API Server with custom routes")
    cache_manager = CacheManager(
        db_path=config.get('database.path', 'data/agent_cache.db'),
        schema_path=config.get('database.schema_path', 'data/schema.sql')
    )
    logger.info("Cache manager initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ADK API Server")
    if cache_manager:
        cache_manager.close()


# Get ADK's FastAPI app
adk_fastapi_app = get_fast_api_app(app=adk_app)

# Create wrapper app with custom routes
app = FastAPI(
    title=config.get('app.name', 'SaaS BI Agent ADK'),
    version=config.get('app.version', '1.0.0'),
    description="Production-grade SaaS BI Agent system with ADK integration",
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

# Mount ADK API Server routes
# ADK routes will be available at their default paths
app.mount("/adk", adk_fastapi_app)

# Include custom routes (maintain existing API structure)
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
app.include_router(cache.router, prefix="/api/v1/cache", tags=["Cache"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])
app.include_router(hitl.router, prefix="/api/v1/hitl", tags=["HITL"])

# Note: Analysis routes will be handled by ADK API Server
# Custom analysis routes can be added here if needed for compatibility


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": config.get('app.name', 'SaaS BI Agent ADK'),
        "version": config.get('app.version', '1.0.0'),
        "status": "running",
        "adk_enabled": True,
        "context_caching": adk_app.context_cache_config is not None
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "cache": "connected" if cache_manager else "disconnected",
        "adk_app": adk_app.name if adk_app else "not_loaded"
    }


if __name__ == "__main__":
    import uvicorn
    
    api_config = {
        'host': config.get('api.host', '0.0.0.0'),
        'port': config.get('api.port', 8000),
        'reload': config.get('api.reload', False)
    }
    
    uvicorn.run(
        "adk_api_main:app",
        host=api_config.get('host', '0.0.0.0'),
        port=api_config.get('port', 8000),
        reload=api_config.get('reload', False)
    )

