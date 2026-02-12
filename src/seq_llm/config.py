"""Configuration management for Sequence-LLM.

This module handles all configuration loading, validation, and model management.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a single LLM model."""

    name: str
    model_type: str
    base_url: str
    api_key: str
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 30
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate model configuration."""
        if not self.name or not self.model_type:
            logger.error("Model name and type are required")
            return False
        if not self.base_url:
            logger.error(f"Model {self.name} missing base_url")
            return False
        if not self.api_key:
            logger.error(f"Model {self.name} missing api_key")
            return False
        return True


@dataclass
class ServerConfig:
    """Configuration for server settings."""

    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    def validate(self) -> bool:
        """Validate server configuration."""
        if not 0 < self.port < 65536:
            logger.error(f"Invalid port: {self.port}")
            return False
        return True


@dataclass
class Config:
    """Main configuration object."""

    server: ServerConfig
    models: Dict[str, ModelConfig]
    default_model: Optional[str] = None

    def validate(self) -> bool:
        """Validate entire configuration."""
        if not self.server.validate():
            return False

        if not self.models:
            logger.error("At least one model must be configured")
            return False

        for model in self.models.values():
            if not model.validate():
                return False

        if self.default_model and self.default_model not in self.models:
            logger.error(f"Default model {self.default_model} not found in models")
            return False

        return True

    def get_model(self, name: Optional[str] = None) -> Optional[ModelConfig]:
        """Get model configuration by name or return default."""
        model_name = name or self.default_model
        if not model_name:
            if self.models:
                return next(iter(self.models.values()))
            return None
        return self.models.get(model_name)


class ConfigLoader:
    """Loads and manages configuration from various sources."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize config loader.

        Args:
            config_path: Path to configuration file. If None, uses default locations.
        """
        self.config_path = config_path or self._find_config_file()

    @staticmethod
    def _find_config_file() -> str:
        """Find configuration file in default locations."""
        default_locations = [
            "config.yaml",
            "config.yml",
            os.path.expanduser("~/.seq_llm/config.yaml"),
            "/etc/seq_llm/config.yaml",
        ]

        for location in default_locations:
            path = Path(location)
            if path.exists():
                logger.info(f"Found config file at {location}")
                return str(path)

        raise FileNotFoundError(
            f"Configuration file not found in default locations: {default_locations}"
        )

    def load(self) -> Config:
        """Load configuration from file.

        Returns:
            Config object

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config is invalid
        """
        path = Path(self.config_path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError("Configuration file is empty")

        return self._parse_config(data)

    def _parse_config(self, data: Dict[str, Any]) -> Config:
        """Parse raw configuration data into Config object.

        Args:
            data: Raw configuration dictionary

        Returns:
            Config object

        Raises:
            ValueError: If configuration is invalid
        """
        # Parse server config
        server_data = data.get('server', {})
        server = ServerConfig(
            host=server_data.get('host', 'localhost'),
            port=server_data.get('port', 8000),
            debug=server_data.get('debug', False),
            log_level=server_data.get('log_level', 'INFO'),
        )

        # Parse models
        models_data = data.get('models', {})
        if not models_data:
            raise ValueError("No models configured")

        models = {}
        for model_name, model_data in models_data.items():
            model = ModelConfig(
                name=model_name,
                model_type=model_data.get('type', 'openai'),
                base_url=model_data.get('base_url', ''),
                api_key=model_data.get('api_key', '') or os.getenv('OPENAI_API_KEY', ''),
                max_tokens=model_data.get('max_tokens', 2048),
                temperature=model_data.get('temperature', 0.7),
                timeout=model_data.get('timeout', 30),
                extra_params=model_data.get('extra_params', {}),
            )
            models[model_name] = model

        # Create config
        config = Config(
            server=server,
            models=models,
            default_model=data.get('default_model'),
        )

        # Validate
        if not config.validate():
            raise ValueError("Configuration validation failed")

        return config

    @staticmethod
    def load_from_dict(data: Dict[str, Any]) -> Config:
        """Load configuration from dictionary (useful for testing).

        Args:
            data: Configuration dictionary

        Returns:
            Config object
        """
        loader = ConfigLoader.__new__(ConfigLoader)
        return loader._parse_config(data)
