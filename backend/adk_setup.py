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
    app_name: Optional[str] = None,
    agent: Optional = None
) -> Runner:
    """
    Get ADK Runner instance configured with session service.
    
    Args:
        session_service: Optional SessionService instance. If None, will create one.
        app_name: Optional app name for the runner
        agent: Optional agent instance (required if app_name is provided)
    
    Returns:
        Configured Runner instance
    
    Note: Runner requires either an App instance or both app_name and agent.
    This function will be updated once agents are created.
    """
    if session_service is None:
        session_service = get_session_service()
    
    # Runner requires either app or (app_name + agent)
    # For now, we'll create a basic runner that can be extended later
    # This will be updated when we create the actual agents
    if app_name and agent:
        runner = Runner(
            session_service=session_service,
            app_name=app_name,
            agent=agent
        )
    else:
        # Create a minimal runner for setup/testing
        # This will be replaced when agents are created
        logger.warning("Runner created without agent. Will need agent/app to be functional.")
        # For now, we can't create a Runner without an agent/app
        # This function will be updated in Phase 3 when agents are created
        raise ValueError("Runner requires either app or both app_name and agent. Agents not yet created.")
    
    logger.info("ADK Runner initialized")
    return runner

