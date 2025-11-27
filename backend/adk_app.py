"""
ADK App Configuration
Exports ADK App with context caching enabled for API Server integration.

This file exports the App object that ADK API Server will discover and use.
Context caching is enabled with compression for better performance.
"""

from google.adk.apps.app import App
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.plugins.reflect_retry_tool_plugin import ReflectAndRetryToolPlugin
from adk_agents.orchestrator import create_main_orchestrator
from utils.logger import logger
from utils.config import config


# Create the main orchestrator agent
root_agent = create_main_orchestrator()

# Disable explicit ADK context caching - using Gemini's implicit caching instead
# 
# Gemini 2.5 Flash has implicit caching that starts at ~1024 tokens:
# - Our ~2000 token system instructions automatically trigger implicit caching
# - No need for explicit cachedContent API (which requires min 4096 tokens)
# - Just need to ensure system instruction prefix remains identical across requests
# - Cached tokens are billed at reduced rate (typically 75% discount)
#
# Benefits of implicit caching:
# - Automatic - no configuration needed
# - Lower threshold (1024 vs 4096 tokens)
# - Works with existing prompts without modification
context_cache_config = None  # Disabled - using Gemini 2.5 Flash implicit caching

# Configure ADK plugins
# ReflectAndRetryToolPlugin: Automatically retries failed tool calls with reflection
# NOTE: Plugins must be configured in the App, not in the Runner when app is provided
plugins = [ReflectAndRetryToolPlugin()]

# Create ADK App with context caching and plugins
# CRITICAL: App name must match inferred app_name from ADK Runner
# ADK Runner infers app_name="agents" from module path (site-packages/google/adk/agents)
# We set app name to "agents" to match the inferred value and avoid session lookup errors
app = App(
    name="agents",  # Must match inferred app_name from Runner module path
    root_agent=root_agent,
    context_cache_config=context_cache_config,
    plugins=plugins  # Plugins configured in App (required when app is provided to Runner)
)

logger.info(f"ADK App created with ReflectAndRetryToolPlugin (model: {config.get('gemini.model', 'gemini-1.5-flash')})")

# Export for ADK API Server discovery
__all__ = ['app', 'root_agent']

