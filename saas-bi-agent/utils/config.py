"""
Configuration management for SaaS BI Agent system.
Loads and validates configuration from YAML file with environment variable overrides.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """Database configuration."""
    path: str = "data/agent_cache.db"
    schema_path: str = "data/schema.sql"
    connection_timeout: int = 30
    enable_wal_mode: bool = True


@dataclass
class CacheConfig:
    """Cache configuration."""
    prompt_ttl_hours: int = 168
    agent_response_ttl_hours: int = 24
    cleanup_interval_hours: int = 6
    max_cache_size_mb: int = 1000


@dataclass
class GeminiConfig:
    """Google Gemini API configuration."""
    model: str = "gemini-2.0-flash-exp"
    fallback_model: str = "gemini-1.5-flash"
    temperature: float = 0.1
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 8192
    safety_settings: Dict[str, str] = field(default_factory=dict)


@dataclass
class APIConfig:
    """API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = True
    log_level: str = "info"
    cors_origins: list = field(default_factory=list)
    max_request_size: int = 10485760


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"
    output: str = "stdout"
    file_path: str = "logs/agent_system.log"
    max_file_size_mb: int = 100
    backup_count: int = 5
    include_trace_id: bool = True
    include_session_id: bool = True


class Config:
    """
    Central configuration manager for the SaaS BI Agent system.

    Loads configuration from YAML file and provides typed access to settings.
    Supports environment variable overrides using the pattern:
    AGENT_SECTION_KEY=value (e.g., AGENT_GEMINI_MODEL=gemini-2.0-flash)
    """

    _instance: Optional['Config'] = None
    _config_data: Dict[str, Any] = {}

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to config.yaml file. If None, searches in common locations.
        """
        if config_path is None:
            config_path = self._find_config_file()

        self.config_path = Path(config_path)
        self._load_config()
        self._apply_env_overrides()

    @classmethod
    def get_instance(cls, config_path: Optional[str] = None) -> 'Config':
        """
        Get singleton instance of Config.

        Args:
            config_path: Optional path to config file

        Returns:
            Config instance
        """
        if cls._instance is None:
            cls._instance = cls(config_path)
        return cls._instance

    @staticmethod
    def _find_config_file() -> str:
        """
        Find config.yaml in common locations.

        Returns:
            Path to config.yaml

        Raises:
            FileNotFoundError: If config.yaml not found
        """
        search_paths = [
            "config.yaml",
            "saas-bi-agent/config.yaml",
            "../config.yaml",
            os.path.join(os.path.dirname(__file__), "..", "config.yaml"),
        ]

        for path in search_paths:
            if os.path.exists(path):
                return path

        raise FileNotFoundError(
            "config.yaml not found. Searched locations: " + ", ".join(search_paths)
        )

    def _load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self._config_data = yaml.safe_load(f) or {}

    def _apply_env_overrides(self):
        """
        Apply environment variable overrides.

        Environment variables should be in the format:
        AGENT_SECTION_KEY=value

        Examples:
            AGENT_GEMINI_MODEL=gemini-2.0-flash
            AGENT_DATABASE_PATH=/custom/path/db.sqlite
        """
        prefix = "AGENT_"

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and split into parts
                parts = key[len(prefix):].lower().split('_')

                if len(parts) >= 2:
                    section = parts[0]
                    config_key = '_'.join(parts[1:])

                    if section in self._config_data:
                        # Try to convert to appropriate type
                        if isinstance(self._config_data[section].get(config_key), bool):
                            value = value.lower() in ('true', '1', 'yes')
                        elif isinstance(self._config_data[section].get(config_key), int):
                            value = int(value)
                        elif isinstance(self._config_data[section].get(config_key), float):
                            value = float(value)

                        self._config_data[section][config_key] = value

    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            section: Configuration section
            key: Optional configuration key within section
            default: Default value if not found

        Returns:
            Configuration value
        """
        if key is None:
            return self._config_data.get(section, default)

        section_data = self._config_data.get(section, {})
        return section_data.get(key, default)

    @property
    def database(self) -> DatabaseConfig:
        """Get database configuration."""
        db_config = self.get('database', default={})
        return DatabaseConfig(
            path=db_config.get('path', 'data/agent_cache.db'),
            schema_path=db_config.get('schema_path', 'data/schema.sql'),
            connection_timeout=db_config.get('connection_timeout', 30),
            enable_wal_mode=db_config.get('enable_wal_mode', True)
        )

    @property
    def cache(self) -> CacheConfig:
        """Get cache configuration."""
        cache_config = self.get('cache', default={})
        return CacheConfig(
            prompt_ttl_hours=cache_config.get('prompt_ttl_hours', 168),
            agent_response_ttl_hours=cache_config.get('agent_response_ttl_hours', 24),
            cleanup_interval_hours=cache_config.get('cleanup_interval_hours', 6),
            max_cache_size_mb=cache_config.get('max_cache_size_mb', 1000)
        )

    @property
    def gemini(self) -> GeminiConfig:
        """Get Gemini API configuration."""
        gemini_config = self.get('gemini', default={})
        return GeminiConfig(
            model=gemini_config.get('model', 'gemini-2.0-flash-exp'),
            fallback_model=gemini_config.get('fallback_model', 'gemini-1.5-flash'),
            temperature=gemini_config.get('temperature', 0.1),
            top_p=gemini_config.get('top_p', 0.95),
            top_k=gemini_config.get('top_k', 40),
            max_output_tokens=gemini_config.get('max_output_tokens', 8192),
            safety_settings=gemini_config.get('safety_settings', {})
        )

    @property
    def api(self) -> APIConfig:
        """Get API server configuration."""
        api_config = self.get('api', default={})
        return APIConfig(
            host=api_config.get('host', '0.0.0.0'),
            port=api_config.get('port', 8000),
            workers=api_config.get('workers', 4),
            reload=api_config.get('reload', True),
            log_level=api_config.get('log_level', 'info'),
            cors_origins=api_config.get('cors_origins', []),
            max_request_size=api_config.get('max_request_size', 10485760)
        )

    @property
    def logging(self) -> LoggingConfig:
        """Get logging configuration."""
        logging_config = self.get('logging', default={})
        return LoggingConfig(
            level=logging_config.get('level', 'INFO'),
            format=logging_config.get('format', 'json'),
            output=logging_config.get('output', 'stdout'),
            file_path=logging_config.get('file_path', 'logs/agent_system.log'),
            max_file_size_mb=logging_config.get('max_file_size_mb', 100),
            backup_count=logging_config.get('backup_count', 5),
            include_trace_id=logging_config.get('include_trace_id', True),
            include_session_id=logging_config.get('include_session_id', True)
        )

    @property
    def app_name(self) -> str:
        """Get application name."""
        return self.get('app', 'name', 'SaaS BI Agent')

    @property
    def app_version(self) -> str:
        """Get application version."""
        return self.get('app', 'version', '1.0.0')

    @property
    def environment(self) -> str:
        """Get environment (development, staging, production)."""
        return self.get('app', 'environment', 'development')

    @property
    def debug(self) -> bool:
        """Get debug mode flag."""
        return self.get('app', 'debug', False)

    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """
        Get configuration for specific agent type.

        Args:
            agent_type: Agent type (revenue, product, support, etc.)

        Returns:
            Agent configuration dict
        """
        agents_config = self.get('agents', default={})
        return agents_config.get(agent_type, {})

    def is_agent_enabled(self, agent_type: str) -> bool:
        """
        Check if agent is enabled.

        Args:
            agent_type: Agent type

        Returns:
            True if enabled
        """
        agent_config = self.get_agent_config(agent_type)
        return agent_config.get('enabled', False)

    def reload(self):
        """Reload configuration from file."""
        self._load_config()
        self._apply_env_overrides()


# Global function to get config instance
def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get the global configuration instance.

    Args:
        config_path: Optional path to config file

    Returns:
        Config instance
    """
    return Config.get_instance(config_path)
