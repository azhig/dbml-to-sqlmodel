"""Configuration management for DBML to Code Generator."""

import json
from pathlib import Path

from pydantic import ValidationError

from ..constants import CONFIG_FILE
from ..models.config_models import AppConfig


class ConfigManager:
    """Manage application configuration."""

    def __init__(self, config_path: Path | None = None):
        """Initialize config manager.

        Args:
            config_path: Path to config file. If None, uses CONFIG_FILE constant in current directory.
        """
        self.config_path = config_path or Path.cwd() / CONFIG_FILE
        self._config: AppConfig | None = None

    def load(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
                self._config = AppConfig(**data)
            except (json.JSONDecodeError, ValidationError, TypeError, OSError):
                # If the config is corrupted or unreadable, recreate the default one
                self._config = AppConfig()
                self.save()
        else:
            # First run - create default config
            self._config = AppConfig()
            self.save()

        return self._config

    def save(self) -> None:
        """Save configuration to file."""
        if self._config is None:
            self._config = AppConfig()

        self.config_path.write_text(
            json.dumps(self._config.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @property
    def config(self) -> AppConfig:
        """Get current configuration."""
        if self._config is None:
            return self.load()
        return self._config

    def update(self, **kwargs: str | Path | bool) -> None:
        """Update configuration values.

        Args:
            **kwargs: Configuration fields to update
        """
        if self._config is None:
            self.load()

        # Update only provided fields
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

        self.save()

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config = AppConfig()
        self.save()

    def is_first_run(self) -> bool:
        """Check if this is the first run (config doesn't exist)."""
        return not self.config_path.exists()
