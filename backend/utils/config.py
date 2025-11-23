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
        # Load environment variables from .env file
        load_dotenv()
        
        # Get project root directory
        project_root = Path(__file__).parent.parent
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
                return os.getenv(env_var, obj)
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


# Global configuration instance
config = Config()

