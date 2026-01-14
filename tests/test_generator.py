import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dbml_to_sqlmodel.core.parser import parse_dbml
from dbml_to_sqlmodel.generator import (
    generate_admin_views,
    generate_all_files,
    generate_main_app,
    generate_requirements,
)
from dbml_to_sqlmodel.models.config_models import AppConfig

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
