"""DBML to Code Generator package."""

__version__ = "0.1.0"

from .cli import app
from .core import generate_single_model

__all__ = ["__version__", "app", "generate_single_model"]
