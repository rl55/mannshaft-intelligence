"""
Unified FastAPI App combining ADK API Server with custom routes.

This file creates a FastAPI app that includes:
1. ADK API Server routes (via get_fast_api_app with lifespan)
2. Custom routes (analysis, sessions, cache, monitoring, HITL)

Run this instead of using `adk api_server` command directly:
    python adk_unified_main.py
    OR
    uvicorn adk_unified_main:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from google.adk.cli.fast_api import get_fast_api_app
from adk_app import app as adk_app
from utils.config import config
from utils.logger import logger
from cache.cache_manager import CacheManager

# Import custom routes
from api.routes import analysis, sessions, cache, monitoring, hitl


# Global cache manager instance
cache_manager: CacheManager = None


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager that adds custom routes to ADK API Server."""
    global cache_manager
    
    # Startup
    logger.info("Starting unified ADK API Server with custom routes")
    cache_manager = CacheManager(
        db_path=config.get('database.path', 'data/agent_cache.db'),
        schema_path=config.get('database.schema_path', 'data/schema.sql')
    )
    logger.info("Cache manager initialized")
    
    # Add custom routes to ADK's FastAPI app
    fastapi_app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
    fastapi_app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
    fastapi_app.include_router(cache.router, prefix="/api/v1/cache", tags=["Cache"])
    fastapi_app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])
    fastapi_app.include_router(hitl.router, prefix="/api/v1/hitl", tags=["HITL"])
    
    logger.info("Custom routes added to ADK API Server")
    
    yield
    
    # Shutdown
    logger.info("Shutting down unified ADK API Server")
    if cache_manager:
        cache_manager.close()


# Get ADK's FastAPI app with our custom lifespan
# This will add our custom routes during startup
app = get_fast_api_app(
    agents_dir=".",  # Current directory (ADK will discover app from adk_app.py)
    web=True,
    allow_origins=config.get('api.cors_origins', ['*']),
    lifespan=lifespan  # Pass our lifespan to add custom routes
)

# Override root endpoint
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
        "adk_unified_main:app",
        host=api_config.get('host', '0.0.0.0'),
        port=api_config.get('port', 8000),
        reload=api_config.get('reload', False)
    )

