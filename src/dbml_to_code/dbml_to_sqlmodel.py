"""Backward compatibility layer for dbml_to_sqlmodel module.

This module maintains backward compatibility with the old monolithic structure
while delegating to the new modular architecture.

DEPRECATED: Use the new imports from core, models, and utils packages instead.
"""

# Re-export models
from .models.schema import ColumnInfo, RelationshipInfo, TableInfo

# Re-export parsing functions
from .core.parser import (
    extract_dbml_defaults,
    extract_dbml_types,
    parse_dbml,
    parse_dbml_enums,
)

# Re-export code generation
from .core.code_generator import generate_single_model, to_class_name

# Re-export utility functions
from .integrations import setdefaultattr

__all__ = [
    "ColumnInfo",
    "RelationshipInfo",
    "TableInfo",
    "extract_dbml_defaults",
    "extract_dbml_types",
    "generate_single_model",
    "parse_dbml",
    "parse_dbml_enums",
    "setdefaultattr",
    "to_class_name",
]
