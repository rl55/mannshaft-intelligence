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
from utils.config import config
from utils.logger import logger


def get_session_service() -> BaseSessionService:
    """
    Get ADK SessionService configured with SQLite backend.
    
    Uses DatabaseSessionService for production (SQLite sync),
    falls back to InMemorySessionService for development.
    """
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
    if session_service is None:
        session_service = get_session_service()
    
    # Import app if not provided
    if app is None:
        from adk_app import app
    
    # Create Runner with App
    # When app is provided, app_name should NOT be provided (ADK requirement)
    runner = Runner(
        session_service=session_service,
        app=app  # Only provide app, not app_name
    )
    
    logger.info(f"ADK Runner initialized with app: {app.name}")
    return runner

