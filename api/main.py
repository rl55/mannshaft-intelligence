"""
FastAPI application for SaaS BI Agent system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from utils.config import config
from utils.logger import logger
from cache.cache_manager import CacheManager

# Import routes
from api.routes import analysis, sessions, cache, monitoring


# Global cache manager instance
cache_manager: CacheManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global cache_manager
    
    # Startup
    logger.info("Starting SaaS BI Agent API")
    cache_manager = CacheManager(
        db_path=config.get('database.path', 'data/agent_cache.db'),
        schema_path=config.get('database.schema_path', 'data/schema.sql')
    )
    logger.info("Cache manager initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SaaS BI Agent API")
    if cache_manager:
        cache_manager.close()


# Create FastAPI application
app_config = config.get_app_config()
api_config = config.get_api_config()

app = FastAPI(
    title=app_config.get('name', 'SaaS BI Agent'),
    version=app_config.get('version', '1.0.0'),
    description="Production-grade SaaS BI Agent system backend",
    lifespan=lifespan
)

# CORS middleware
cors_origins = api_config.get('cors_origins', ['*'])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
app.include_router(cache.router, prefix="/api/v1/cache", tags=["Cache"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": app_config.get('name', 'SaaS BI Agent'),
        "version": app_config.get('version', '1.0.0'),
        "status": "running"
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
    
    uvicorn.run(
        "api.main:app",
        host=api_config.get('host', '0.0.0.0'),
        port=api_config.get('port', 8000),
        reload=api_config.get('reload', False)
    )

