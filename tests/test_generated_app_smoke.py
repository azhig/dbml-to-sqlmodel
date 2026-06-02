"""Smoke tests that exercise the *generated* application output.

The other test modules assert on the generator's string output. These tests
guard against regressions where the generator emits code that is broken in
practice (syntax errors, deprecated APIs, wrong types, unsatisfiable
requirements) even though those string assertions still pass.

Only the generator itself is exercised — the generated app's runtime
dependencies (fastapi, sqlmodel, ...) are *not* required to run these tests.
"""

import compileall
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dbml_to_sqlmodel.generator import generate_all_files

SCHEMA = """
Enum post_status {
    draft
    published
}

Table users {
    id serial [pk]
    email text [not null, unique]
    created_at timestamp [not null]
}

Table post_tags {
    id serial [pk]
    user_id integer [ref: > users.id]
    status post_status
    tagged_on date
}
"""


def _write_files(files: dict[str, str], root: Path) -> None:
    for rel_path, content in files.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_generated_files_are_valid_python(tmp_path):
    """Every generated .py file must at least compile."""
    files = generate_all_files(SCHEMA, admin_auth_enabled=True)
    _write_files(files, tmp_path)
    # compile_dir returns True only if every file compiled without errors.
    assert compileall.compile_dir(str(tmp_path), quiet=1)


def test_generated_main_uses_env_and_lifespan():
    """main.py must read DATABASE_URL from the env and use the lifespan API."""
    main = generate_all_files(SCHEMA)["main.py"]
    assert 'os.getenv("DATABASE_URL"' in main
    assert "lifespan=lifespan" in main
    # Deprecated FastAPI startup hook must not be emitted.
    assert "on_event" not in main


def test_generated_models_map_temporal_types():
    """Temporal DBML types must become datetime/date, not str."""
    files = generate_all_files(SCHEMA)

    user_model = files["models/users/model.py"]
    assert "from datetime import datetime" in user_model
    assert "created_at: datetime" in user_model

    post_model = files["models/post_tags/model.py"]
    assert "from datetime import date" in post_model
    # Multi-word table names become proper PascalCase class names.
    assert "class PostTags(" in post_model
    assert "class Post_tags(" not in post_model


def test_generated_requirements_are_satisfiable():
    """requirements.txt must not pin versions that do not exist."""
    reqs = generate_all_files(SCHEMA)["requirements.txt"]
    for package in ("fastapi", "sqlmodel", "sqladmin", "fastcrud", "aiosqlite"):
        assert package in reqs
    # Regression guard: sqladmin never had a 1.x release.
    assert "sqladmin>=1." not in reqs
    assert "sqladmin>=0.22.0" in reqs
    # The async SQLAlchemy engine needs greenlet, which is not auto-installed
    # on every platform/Python combination (e.g. Python 3.13 on macOS arm64).
    assert "greenlet" in reqs
