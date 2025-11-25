"""
ADK App with Custom Routes Integration
This file extends adk_app.py to add custom routes to ADK API Server.

When ADK API Server runs, it will discover this app and use it.
Custom routes are added via lifespan hook.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adk_app import app as adk_app
from utils.config import config
from utils.logger import logger
from cache.cache_manager import CacheManager

# Import custom routes
from api.routes import analysis, sessions, cache, monitoring, hitl


# Global cache manager instance
cache_manager: CacheManager = None


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Lifespan manager that adds custom routes to ADK API Server."""
    global cache_manager
    
    # Startup
    logger.info("Adding custom routes to ADK API Server")
    
    # Initialize cache manager
    cache_manager = CacheManager(
        db_path=config.get('database.path', 'data/agent_cache.db'),
        schema_path=config.get('database.schema_path', 'data/schema.sql')
    )
    logger.info("Cache manager initialized")
    
    # Add CORS middleware if not already present
    cors_origins = config.get('api.cors_origins', ['*'])
    if not any(isinstance(middleware, CORSMiddleware) for middleware in fastapi_app.user_middleware):
        fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS middleware added")
    
    # Include custom routes
    fastapi_app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
    fastapi_app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
    fastapi_app.include_router(cache.router, prefix="/api/v1/cache", tags=["Cache"])
    fastapi_app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])
    fastapi_app.include_router(hitl.router, prefix="/api/v1/hitl", tags=["HITL"])
    
    logger.info("Custom routes added to ADK API Server")
    
    yield
    
    # Shutdown
    logger.info("Shutting down custom routes")
    if cache_manager:
        cache_manager.close()


# Export app with lifespan for ADK API Server
# ADK API Server will use this lifespan to add our custom routes
app = adk_app

# Note: The lifespan will be passed to ADK API Server via command line or config
# For now, we'll need to modify how ADK API Server is invoked

__all__ = ['app', 'lifespan']

