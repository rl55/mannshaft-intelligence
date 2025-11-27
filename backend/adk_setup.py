"""
ADK Infrastructure Setup
Configures ADK runtime components: SessionService, caching, API Server
"""

import os
from pathlib import Path
from typing import Optional

from google.adk import Runner
from google.adk.sessions import (
    BaseSessionService,
    DatabaseSessionService,
    InMemorySessionService,
)
from google.adk.plugins import ReflectAndRetryToolPlugin
from utils.config import config
from utils.logger import logger


def _configure_adk_retries():
    """
    Configure ADK retry mechanism via environment variables.
    
    ADK supports retry configuration through environment variables:
    - AGENT_CLIENT_MAX_RETRIES: Maximum retry attempts (default: 3)
    - AGENT_CLIENT_TIMEOUT: Request timeout duration (default: 30s)
    
    These are set from config.yaml or environment variables.
    """
    # Get retry configuration from config or use defaults
    max_retries = config.get('gemini.max_retries', 3)
    timeout_seconds = config.get('gemini.timeout', 30)
    
    # Set ADK environment variables if not already set
    if 'AGENT_CLIENT_MAX_RETRIES' not in os.environ:
        os.environ['AGENT_CLIENT_MAX_RETRIES'] = str(max_retries)
        logger.info(f"ADK retry configured: AGENT_CLIENT_MAX_RETRIES={max_retries}")
    
    if 'AGENT_CLIENT_TIMEOUT' not in os.environ:
        # ADK expects timeout in format like "30s"
        os.environ['AGENT_CLIENT_TIMEOUT'] = f"{timeout_seconds}s"
        logger.info(f"ADK timeout configured: AGENT_CLIENT_TIMEOUT={timeout_seconds}s")


def get_session_service() -> BaseSessionService:
    """
    Get ADK SessionService configured with SQLite backend.
    
    Uses DatabaseSessionService for production (SQLite sync),
    falls back to InMemorySessionService for development.
    """
    # Configure ADK retries before initializing services
    _configure_adk_retries()
    
    db_path = config.get('database.path', 'data/agent_cache.db')
    
    # Ensure database directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Use DatabaseSessionService with SQLite
        # ADK will create its own session tables if they don't exist
        # Database URL format: sqlite:///path/to/database.db
        session_service = DatabaseSessionService(
            db_url=f"sqlite:///{db_path}"
        )
        logger.info(f"ADK SessionService initialized with SQLite: {db_path}")
        return session_service
    except Exception as e:
        logger.warning(f"Failed to initialize DatabaseSessionService: {e}. Using InMemorySessionService.")
        return InMemorySessionService()


def get_runner(
    session_service: Optional[BaseSessionService] = None,
    app: Optional = None
) -> Runner:
    """
    Get ADK Runner instance configured with session service and app.
    
    Args:
        session_service: Optional SessionService instance. If None, will create one.
        app: Optional ADK App instance. If None, will import from adk_app.
    
    Returns:
        Configured Runner instance ready to execute agents
    
    Usage:
        from adk_setup import get_runner
        from adk_app import app
        
        runner = get_runner(app=app)
        result = await runner.run_async(
            agent=app.root_agent,
            context={"week_number": 10},
            session_id="session-123"
        )
    """
    # Configure ADK retries before creating Runner
    _configure_adk_retries()
    
    if session_service is None:
        session_service = get_session_service()
    
    # Import app if not provided
    if app is None:
        from adk_app import app
    
    # Create Runner with App
    # When app is provided, app_name should NOT be provided (ADK requirement)
    # However, ADK Runner infers app_name from agent module path
    # SequentialAgent is loaded from site-packages/google/adk/agents, so app_name is "agents"
    # We must ensure the App's name matches the inferred app_name, or create sessions with inferred app_name
    
    # NOTE: Plugins must be configured in the App, not in the Runner when app is provided
    # Plugins are already configured in adk_app.py (ReflectAndRetryToolPlugin)
    
    runner = Runner(
        session_service=session_service,
        app=app  # Only provide app, not app_name or plugins (plugins are in app)
    )
    
    # Log plugins from app (if available)
    plugin_names = []
    if hasattr(app, 'plugins') and app.plugins:
        plugin_names = [p.__class__.__name__ for p in app.plugins]
    
    logger.info(f"ADK Runner initialized with app: {app.name}" + (f" and plugins: {plugin_names}" if plugin_names else ""))
    return runner

