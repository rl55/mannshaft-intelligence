"""
Configuration management for SaaS BI Agent system.
Loads configuration from config.yaml and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config:
    """Centralized configuration manager."""
    
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from config.yaml and environment variables."""
        # Get project root directory
        project_root = Path(__file__).parent.parent
        
        # Load environment variables from .env file (in backend directory)
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        else:
            # Fallback to default dotenv behavior
            load_dotenv()
        
        config_path = project_root / "config.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Load YAML configuration
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
        
        # Override with environment variables
        self._override_with_env()
    
    def _override_with_env(self):
        """Override configuration values with environment variables."""
        # Replace ${VAR} placeholders with environment variables
        def replace_env_vars(obj):
            if isinstance(obj, dict):
                return {k: replace_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_env_vars(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                env_var = obj[2:-1]
                env_value = os.getenv(env_var)
                if env_value is None:
                    # Log warning but keep placeholder to help identify missing env vars
                    import warnings
                    warnings.warn(f"Environment variable {env_var} not found, using placeholder")
                    return obj  # Keep original placeholder
                return env_value
            return obj
        
        self._config = replace_env_vars(self._config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'api.port')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration."""
        return self._config.get('app', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        return self._config.get('api', {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self._config.get('database', {})
    
    def get_gemini_config(self) -> Dict[str, Any]:
        """Get Gemini configuration."""
        return self._config.get('gemini', {})
    
    def get_google_sheets_config(self) -> Dict[str, Any]:
        """Get Google Sheets configuration."""
        return self._config.get('google_sheets', {})
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration."""
        return self._config.get('cache', {})
    
    def get_agents_config(self) -> Dict[str, Any]:
        """Get agents configuration."""
        return self._config.get('agents', {})
    
    def get_governance_config(self) -> Dict[str, Any]:
        """Get governance configuration."""
        return self._config.get('governance', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self._config.get('logging', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return self._config.get('monitoring', {})

    def get_model_config_with_retries(self) -> Dict[str, Any]:
        """
        Get model configuration with retry options for Gemini API.

        Returns dict with generate_content_config that includes http_options
        configured for retries on transient errors.
        This should be unpacked when creating LlmAgent.
        """
        from google.genai import types as genai_types

        max_retries = self.get('gemini.max_retries', 5)
        timeout = self.get('gemini.timeout', 60)  # Minimum 10s required by Gemini API

        # Configure retry options for transient errors (503, 429, 500, timeouts)
        retry_options = genai_types.HttpRetryOptions(
            attempts=max_retries,
            initial_delay=2.0,  # Start with 2 second delay (min is 1s, but be safe)
            max_delay=30.0,     # Max 30 seconds between retries
            exp_base=2.0,       # Exponential backoff (2^n)
            jitter=0.1,         # 10% random jitter to avoid thundering herd
            http_status_codes=[429, 500, 502, 503, 504]  # Retry on these status codes
        )

        # Note: Don't set timeout in HttpOptions as it creates per-request deadline
        # The retry_options will handle timing automatically
        http_options = genai_types.HttpOptions(
            retry_options=retry_options
        )

        # Create GenerateContentConfig with http_options
        generate_content_config = genai_types.GenerateContentConfig(
            http_options=http_options
        )

        return {
            'generate_content_config': generate_content_config
        }


# Global configuration instance
config = Config()

