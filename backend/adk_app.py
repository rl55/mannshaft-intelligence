"""
ADK App Configuration
Exports ADK App with context caching enabled for API Server integration.

This file exports the App object that ADK API Server will discover and use.
Context caching is enabled with compression for better performance.
"""

from google.adk.apps.app import App
from google.adk.agents.context_cache_config import ContextCacheConfig
from adk_agents.orchestrator import create_main_orchestrator
from utils.logger import logger
from utils.config import config


# Create the main orchestrator agent
root_agent = create_main_orchestrator()

# Configure context caching with compression
# ADK context caching provides built-in compression for better performance
# ContextCacheConfig is created with default settings (caching enabled by default)
context_cache_config = ContextCacheConfig()

# Create ADK App with context caching
app = App(
    name="saas_bi_agent_adk",
    root_agent=root_agent,
    context_cache_config=context_cache_config
)

logger.info("ADK App created with context caching enabled")

# Export for ADK API Server discovery
__all__ = ['app', 'root_agent']

