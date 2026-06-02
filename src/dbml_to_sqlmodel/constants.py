"""Project-wide constants."""

# Configuration file name (stored in the working directory)
CONFIG_FILE = ".dbml_to_sqlmodel"

# Marker used to protect manually edited generated files from being overwritten
USER_FILE_MARKER = "# USER_MODIFIED"
PROTECTED_FILE_WARNING = """# USER_MODIFIED
# This file has been manually modified and is protected from regeneration.
# Remove this marker if you want to allow regeneration.
"""
