"""Backward compatibility layer for config module.

This module maintains backward compatibility with the old config.py
while delegating to the new modular architecture.

DEPRECATED: Use the new imports from core.config and models.config_models instead.
"""

# Re-export configuration models and manager
from .models.config_models import AppConfig
from .core.config import ConfigManager

__all__ = [
    "AppConfig",
    "ConfigManager",
]
