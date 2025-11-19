"""
Main FastAPI application for SaaS BI Agent system.

This module initializes the FastAPI app, sets up middleware, routes, and lifecycle hooks.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import uvicorn

from api.routes import analysis, sessions, cache, monitoring
from api.models.responses import ErrorResponse
from utils.config import get_config
from utils.logger import setup_logging, get_logger, set_trace_context, clear_trace_context
from cache.cache_manager import CacheManager

import uuid
import sys


# Initialize configuration
config = get_config()

# Setup logging
setup_logging(
    level=config.logging.level,
    log_format=config.logging.format,
    output=config.logging.output,
    file_path=config.logging.file_path,
    max_file_size_mb=config.logging.max_file_size_mb,
    backup_count=config.logging.backup_count
)

logger = get_logger(__name__)


# Global cache manager instance
cache_manager: CacheManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting SaaS BI Agent API...")

    try:
        # Initialize cache manager
        global cache_manager
        cache_manager = CacheManager(
            db_path=config.database.path,
            schema_path=config.database.schema_path
        )
        cache_manager.connect()
        logger.info("✓ Cache manager initialized")

        # TODO: Initialize agents when implemented
        # - Revenue Agent
        # - Product Agent
        # - Support Agent
        # - Synthesizer Agent
        # - Orchestrator

        logger.info("✓ SaaS BI Agent API started successfully")

    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        sys.exit(1)

    yield

    # Shutdown
    logger.info("Shutting down SaaS BI Agent API...")

    try:
        if cache_manager:
            cache_manager.close()
            logger.info("✓ Cache manager closed")

        logger.info("✓ SaaS BI Agent API shut down successfully")

    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="""
    SaaS BI Agent System - Production-grade multi-agent business intelligence platform.

    Features:
    - Multi-agent orchestration (Revenue, Product, Support, Synthesizer)
    - Intelligent caching for performance optimization
    - Distributed tracing and observability
    - Governance and guardrails
    - Human-in-the-loop escalation
    - Automated evaluation and quality control

    Powered by Google Gemini and built with FastAPI.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_and_logging(request: Request, call_next):
    """
    Middleware to add request ID and trace context to all requests.
    """
    # Generate request ID
    request_id = str(uuid.uuid4())

    # Set trace context
    set_trace_context(trace_id=request_id)

    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra_data={
            'method': request.method,
            'path': request.url.path,
            'client': request.client.host if request.client else None,
            'request_id': request_id
        }
    )

    # Add request ID to response headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    # Clear trace context
    clear_trace_context()

    return response


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(
        f"Validation error: {str(exc)}",
        extra_data={
            'errors': exc.errors(),
            'body': str(exc.body)
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "error_type": "RequestValidationError",
            "timestamp": datetime.utcnow().isoformat(),
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra_data={
            'path': request.url.path,
            'method': request.method
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "error_type": type(exc).__name__,
            "timestamp": datetime.utcnow().isoformat(),
            "details": str(exc) if config.debug else None
        }
    )


# ============================================================================
# ROUTES
# ============================================================================

# Include routers
app.include_router(analysis.router)
app.include_router(sessions.router)
app.include_router(cache.router)
app.include_router(monitoring.router)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": config.app_name,
        "version": config.app_version,
        "status": "online",
        "environment": config.environment,
        "docs": "/docs",
        "health": "/monitoring/health"
    }


# ============================================================================
# DEPENDENCY INJECTION HELPERS
# ============================================================================

def get_cache_manager() -> CacheManager:
    """
    Dependency to get cache manager instance.

    Returns:
        CacheManager instance

    Raises:
        RuntimeError: If cache manager not initialized
    """
    if cache_manager is None:
        raise RuntimeError("Cache manager not initialized")
    return cache_manager


# ============================================================================
# RUN SERVER
# ============================================================================

def run_server():
    """
    Run the FastAPI server using uvicorn.
    """
    uvicorn.run(
        "api.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.reload,
        log_level=config.api.log_level.lower(),
        workers=1 if config.api.reload else config.api.workers
    )


if __name__ == "__main__":
    run_server()
