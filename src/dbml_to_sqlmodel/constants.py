"""Project-wide constants."""

# Default paths
DEFAULT_SCHEMA_PATH = "schemas/schema.dbml"
DEFAULT_OUTPUT_DIR = "output"
CONFIG_FILE = ".dbml_to_sqlmodel"

# File markers
USER_FILE_MARKER = "# USER_MODIFIED"
PROTECTED_FILE_WARNING = """# USER_MODIFIED
# This file has been manually modified and is protected from regeneration.
# Remove this marker if you want to allow regeneration.
"""

# Server defaults
DEFAULT_SERVER_PORT = 8001
DEFAULT_SERVER_HOST = "0.0.0.0"

# Admin panel
ADMIN_PATH = "/admin"
ADMIN_TITLE = "Admin Panel"

# Database
DEFAULT_DB_NAME = "app.db"
DEFAULT_DB_URL_TEMPLATE = "sqlite:///{db_name}"
