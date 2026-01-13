import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dbml_to_code.dbml_to_sqlmodel import parse_dbml
from dbml_to_code.generator import (
    generate_admin_views,
    generate_all_files,
    generate_main_app,
    generate_requirements,
)
from dbml_to_code.config import AppConfig


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
