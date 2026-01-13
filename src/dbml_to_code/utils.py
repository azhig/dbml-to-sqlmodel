"""Backward compatibility layer for utils module.

This module maintains backward compatibility with the old monolithic utils.py
while delegating to the new modular architecture.

DEPRECATED: Use the new imports from utils package submodules instead.
"""

# Re-export constants
from .constants import PROTECTED_FILE_WARNING, USER_FILE_MARKER

# Re-export file management functions
from .utils.file_manager import (
    calculate_file_status,
    get_user_modified_files,
    is_user_modified,
    mark_as_user_modified,
)

# Re-export diff functions
from .utils.diff import (
    apply_diff_to_file,
    generate_diff,
    normalize_model_code,
    print_diff,
)

# Re-export formatters
from .utils.formatters import print_file_status_table

# Re-export console from Rich (commonly used with these utils)
from rich.console import Console

console = Console()

__all__ = [
    "PROTECTED_FILE_WARNING",
    "USER_FILE_MARKER",
    "apply_diff_to_file",
    "calculate_file_status",
    "console",
    "generate_diff",
    "get_user_modified_files",
    "is_user_modified",
    "mark_as_user_modified",
    "normalize_model_code",
    "print_diff",
    "print_file_status_table",
]
