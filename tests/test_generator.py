import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dbml_to_sqlmodel.core import parser as parser_module
from dbml_to_sqlmodel.core.parser import parse_dbml
from dbml_to_sqlmodel.generator import (
    generate_admin_views,
    generate_all_files,
    generate_enums_file,
    generate_main_app,
    generate_requirements,
)
from dbml_to_sqlmodel.models.config_models import AppConfig
from dbml_to_sqlmodel.models.schema import ColumnInfo, TableInfo

DBML_SAMPLE = """
Table users {
    id serial [pk]
    name text
}
"""


def test_generate_admin_views_auth_disabled():
    tables = parse_dbml(DBML_SAMPLE)
    code = generate_admin_views(tables, admin_auth_enabled=False)

    assert "AuthenticationBackend" not in code
    assert "SessionMiddleware" not in code
    assert "class AdminAuth" not in code
    assert "authentication_backend" not in code
    assert "admin = Admin(app, engine)" in code


def test_generate_admin_views_auth_enabled():
    tables = parse_dbml(DBML_SAMPLE)
    code = generate_admin_views(tables, admin_auth_enabled=True)

    assert "AuthenticationBackend" in code
    assert "SessionMiddleware" in code
    assert "class AdminAuth" in code
    assert "authentication_backend=auth" in code


def test_generate_all_files_with_admin_auth():
    files = generate_all_files(DBML_SAMPLE, admin_auth_enabled=True)
    assert "admin.py" in files
    assert "AuthenticationBackend" in files["admin.py"]


def test_generate_main_app_includes_dotenv_loader():
    tables = parse_dbml(DBML_SAMPLE)
    code = generate_main_app(tables)

    assert "from dotenv import load_dotenv" in code
    assert "load_dotenv()" in code


def test_generate_requirements_includes_dotenv():
    requirements = generate_requirements()
    assert "python-dotenv" in requirements


def test_app_config_admin_auth_default_disabled():
    config = AppConfig()
    assert config.admin_auth_enabled is False


def test_generate_main_app_basic():
    """Test generating basic main app."""
    tables = parse_dbml(DBML_SAMPLE)
    code = generate_main_app(tables)

    assert "from fastapi import FastAPI" in code
    assert "from dotenv import load_dotenv" in code
    assert "load_dotenv()" in code
    assert "app = FastAPI" in code


def test_generate_requirements_contains_expected_packages():
    """Test that requirements contains expected packages."""
    requirements = generate_requirements()

    assert "fastapi" in requirements
    assert "sqlmodel" in requirements
    assert "fastcrud" in requirements
    assert "sqladmin" in requirements
    assert "python-dotenv" in requirements
    assert "aiosqlite" in requirements


def test_generate_all_files_contains_expected_files():
    """Test that generate_all_files creates expected file structure."""
    files = generate_all_files(DBML_SAMPLE, admin_auth_enabled=False)

    assert "main.py" in files
    assert "admin.py" in files
    assert "requirements.txt" in files
    assert any("users" in path for path in files.keys())


def test_generate_all_files_without_admin_auth():
    """Test generation without admin auth."""
    files = generate_all_files(DBML_SAMPLE, admin_auth_enabled=False)

    assert "admin.py" in files
    assert "AuthenticationBackend" not in files["admin.py"]


def test_generate_admin_views_without_tables():
    """Test admin views generation with empty table list."""
    code = generate_admin_views([], admin_auth_enabled=False)

    assert "from sqladmin import Admin" in code
    assert "admin = Admin" in code


def test_generate_all_files_multiple_tables():
    """Test generation with multiple tables."""
    dbml = """
    Table users {
        id serial [pk]
        name text
    }
    Table posts {
        id serial [pk]
        title text
    }
    """
    files = generate_all_files(dbml, admin_auth_enabled=False)

    # Should have model files for both tables
    assert any("users" in path for path in files.keys())
    assert any("posts" in path for path in files.keys())


def test_extract_enums_and_admin_views():
    dbml = """
    Enum status {
        active
        disabled
    }
    """
    enums = parser_module.parse_dbml_enums(dbml)
    assert enums == {"status": ["active", "disabled"]}

    tables = parser_module.parse_dbml("Table users {\n    id integer [pk]\n}\n")
    auth_code = generate_admin_views(tables, admin_auth_enabled=True)
    no_auth_code = generate_admin_views(tables, admin_auth_enabled=False)
    assert "AuthenticationBackend" in auth_code
    assert "AuthenticationBackend" not in no_auth_code


def test_admin_views_labels_and_searchable():
    table = TableInfo(
        name="users",
        columns=[
            ColumnInfo(
                name="name",
                type="text",
                primary_key=False,
                unique=False,
                nullable=False,
                note="Full name",
            ),
            ColumnInfo(
                name="age",
                type="integer",
                primary_key=False,
                unique=False,
                nullable=True,
            ),
        ],
    )
    code = generate_admin_views([table], admin_auth_enabled=False)
    assert "column_labels" in code
    assert "column_searchable_list" in code


def test_generate_admin_views_labels_and_searchable():
    table = TableInfo(
        name="users",
        columns=[
            ColumnInfo(
                name="name",
                type="varchar",
                primary_key=False,
                unique=False,
                nullable=False,
                note="Full name",
            ),
            ColumnInfo(
                name="age",
                type="integer",
                primary_key=False,
                unique=False,
                nullable=True,
            ),
        ],
    )
    code = generate_admin_views([table], admin_auth_enabled=True)
    assert "column_labels" in code
    assert "column_searchable_list" in code


def test_generator_enums_and_invalid_values():
    enums = parser_module.parse_dbml_enums(
        """
        enum status {
            active,
            1st-place
            // comment
        }
        """
    )
    assert enums == {"status": ["active", "1st-place"]}

    content = generate_enums_file({"status": ["active", "1st-place"]})
    assert "class Status" in content
    assert "VALUE_1ST_PLACE" in content


def test_generate_all_files_with_enums():
    dbml = """
    Enum status {
        active
    }
    Table users {
        id integer [pk]
        status status
    }
    """
    files = generate_all_files(dbml, admin_auth_enabled=False)
    assert "models/enums.py" in files


def test_generate_all_files_no_tables():
    with pytest.raises(ValueError):
        generate_all_files("// empty")
