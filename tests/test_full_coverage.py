import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest
import typer

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dbml_to_sqlmodel import cli as cli_module
from dbml_to_sqlmodel import generate_app
from dbml_to_sqlmodel.commands import code_to_dbml, generate, info, preview
from dbml_to_sqlmodel.constants import USER_FILE_MARKER
from dbml_to_sqlmodel.core import parser as parser_module
from dbml_to_sqlmodel.core.code_generator import generate_single_model
from dbml_to_sqlmodel.generator import (
    _extract_enums_from_text,
    generate_admin_views,
    generate_all_files,
    generate_enums_file,
)
from dbml_to_sqlmodel.models.file_info import FileInfo, FileStatus
from dbml_to_sqlmodel.models.schema import ColumnInfo, TableInfo
from dbml_to_sqlmodel.sqlmodel_to_dbml import (
    _annotation_to_type,
    _canonical_dbml_type,
    _columns_equivalent,
    _extract_columns,
    _format_dbml_column,
    _format_table_header,
    _format_table_header_like,
    _model_files,
    _parse_field_kwargs,
    _parse_model_file,
    _table_name_from_path,
    apply_dbml_changes,
    apply_dbml_table_updates,
    apply_schema_hints,
    canonicalize_dbml_text,
    generate_dbml_from_models,
    normalize_dbml,
    normalize_dbml_for_compare,
)
from dbml_to_sqlmodel.utils import diff as diff_module


def _write_model(tmp_path: Path, rel_path: str, content: str) -> Path:
    file_path = tmp_path / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _dbml_sample_tables() -> str:
    return """
Table users {
    id integer [pk]
    name text
}
Table teams {
    id integer [pk]
    name text
}
Table projects {
    id integer [pk]
    name text
}
Table notes {
    id integer [pk]
    body text
}
"""


def test_file_info_status_tuple():
    info_obj = FileInfo("a.py", FileStatus.CREATED, True)
    assert info_obj.status_tuple == ("created", True)


def test_generate_app_main_success(tmp_path, monkeypatch):
    dbml_path = tmp_path / "schema.dbml"
    dbml_path.write_text(
        "Enum status {\n    active\n}\nTable users {\n    id integer [pk]\n    status status\n}\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "out"
    monkeypatch.setattr(
        sys,
        "argv",
        ["generate_app.py", str(dbml_path), "-o", str(output_dir)],
    )

    generate_app.main()

    assert (output_dir / "main.py").exists()
    assert (output_dir / "models" / "enums.py").exists()
    assert (output_dir / "models" / "users" / "model.py").exists()


def test_generate_app_main_module_run(tmp_path):
    dbml_path = tmp_path / "schema.dbml"
    dbml_path.write_text(
        "Table users {\n    id integer [pk]\n}\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "out"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "dbml_to_sqlmodel.generate_app",
            str(dbml_path),
            "-o",
            str(output_dir),
        ],
        check=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert (output_dir / "main.py").exists()


def test_generate_app_main_no_tables(tmp_path, monkeypatch):
    dbml_path = tmp_path / "schema.dbml"
    dbml_path.write_text("", encoding="utf-8")

    output_dir = tmp_path / "out"
    monkeypatch.setattr(
        sys,
        "argv",
        ["generate_app.py", str(dbml_path), "-o", str(output_dir)],
    )

    with pytest.raises(SystemExit):
        generate_app.main()


def test_cli_app_error_paths(monkeypatch):
    def raise_keyboard():
        raise KeyboardInterrupt

    monkeypatch.setattr(cli_module, "interactive_menu", raise_keyboard)
    cli_module.app()

    def raise_error():
        raise ValueError("boom")

    monkeypatch.setattr(cli_module, "interactive_menu", raise_error)
    with pytest.raises(ValueError):
        cli_module.app()


def test_generate_app_extract_enums_and_admin_views():
    dbml = """
    Enum status {
        active
        disabled
    }
    """
    enums = generate_app._extract_enums_from_text(dbml)
    assert enums == {"status": ["active", "disabled"]}

    tables = parser_module.parse_dbml("Table users {\n    id integer [pk]\n}\n")
    auth_code = generate_app.generate_admin_views(tables, admin_auth_enabled=True)
    no_auth_code = generate_app.generate_admin_views(tables, admin_auth_enabled=False)
    assert "AuthenticationBackend" in auth_code
    assert "AuthenticationBackend" not in no_auth_code


def test_generate_app_admin_views_labels_and_searchable():
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
    code = generate_app.generate_admin_views([table], admin_auth_enabled=False)
    assert "column_labels" in code
    assert "column_searchable_list" in code


def test_generator_enums_and_invalid_values():
    enums = _extract_enums_from_text(
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


def test_generate_single_model_edge_cases():
    enum_table = TableInfo(
        name="widgets",
        columns=[
            ColumnInfo(
                name="id",
                type="bool",
                primary_key=True,
                unique=False,
                nullable=False,
                note="id note",
            ),
            ColumnInfo(
                name="status",
                type="status",
                primary_key=True,
                unique=False,
                nullable=False,
            ),
        ],
        note='note """ triple',
    )
    rel_table = TableInfo(
        name="posts",
        columns=[
            ColumnInfo(
                name="user_id",
                type="integer",
                primary_key=False,
                unique=False,
                nullable=False,
                references=[("users", "id")],
            ),
        ],
    )
    nopk_table = TableInfo(
        name="logs",
        columns=[
            ColumnInfo(
                name="message",
                type="text",
                primary_key=False,
                unique=False,
                nullable=True,
            ),
        ],
    )
    all_tables = [enum_table, rel_table, nopk_table]
    enums = {"status": ["active"]}

    enum_code = generate_single_model(enum_table, all_tables, enums=enums)
    assert '"""note \\"\\"\\" triple"""' in enum_code
    assert "DESCRIPTIONS" in enum_code
    assert 'description=DESCRIPTIONS["id"]' in enum_code
    assert "status: Status" in enum_code

    rel_code = generate_single_model(rel_table, all_tables, enums=enums)
    assert "Relationship()" in rel_code

    nopk_code = generate_single_model(nopk_table, all_tables, enums=enums)
    assert "class Logs(LogsBase, table=True):\n    pass" in nopk_code


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


def test_generate_all_files_no_tables():
    with pytest.raises(ValueError):
        generate_all_files("// empty")


def test_extract_dbml_types_and_defaults():
    dbml = """
    // comment
    Table users
    {
        id integer [default: 1]
        name varchar(255) [default: "bob"]
        active boolean [default: true]
        disabled boolean [default: false]
        ratio float [default: 1.5]
        weird integer [nodefault=3]
        // inside comment
        invalid_only_name
        note: 'ignored'
        indexes {
            name
        }
    }
    Ref: users.id > other.id
    """
    types = parser_module.extract_dbml_types(dbml)
    defaults = parser_module.extract_dbml_defaults(dbml)

    assert types["users"]["name"] == "varchar(255)"
    assert defaults["users"]["id"] == 1
    assert defaults["users"]["name"] == "bob"
    assert defaults["users"]["active"] is True
    assert defaults["users"]["disabled"] is False
    assert defaults["users"]["ratio"] == 1.5


def test_parse_dbml_enums_from_text():
    dbml = """
    enum status {
        active,
        disabled // trailing
    }
    """
    enums = parser_module.parse_dbml_enums(dbml)
    assert enums == {"status": ["active", "disabled"]}


def test_parse_dbml_enums_missing_name(monkeypatch):
    class FakeEnum:
        def __init__(self, name, items):
            self.name = name
            self.items = items

    class FakeItem:
        def __init__(self, name):
            self.name = name

    class FakeParsed:
        enums = [FakeEnum(None, [FakeItem("skip")]), FakeEnum("Status", [FakeItem("active")])]

    monkeypatch.setattr(parser_module, "_parse_dbml_enums_from_text", lambda _text: {})
    monkeypatch.setattr(parser_module, "PyDBML", lambda _text: FakeParsed())

    enums = parser_module.parse_dbml_enums("enum status { active }")
    assert enums == {"Status": ["active"]}


def test_parse_dbml_with_fake_pydbml(monkeypatch):
    class FakeType:
        def __init__(self, name):
            self.name = name

    class NoteNoText:
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return self.value

    class FakeColumn:
        def __init__(
            self, name, col_type, pk=False, unique=False, not_null=False, default=None, note=None
        ):
            self.name = name
            self.type = col_type
            self.pk = pk
            self.unique = unique
            self.not_null = not_null
            self.default = default
            self.note = note

    class FakeTable:
        def __init__(self, name, columns, note=None):
            self.name = name
            self.columns = columns
            self.note = note

    class FakeRef:
        def __init__(self, ref_type, col1, col2, table1, table2):
            self.type = ref_type
            self.col1 = col1
            self.col2 = col2
            self.table1 = table1
            self.table2 = table2

    users_id = FakeColumn("id", FakeType("int"), pk=True, note=NoteNoText("id note"))
    posts_user_id = FakeColumn("user_id", "integer", not_null=True)

    users_table = FakeTable("users", [users_id], note=NoteNoText("users note"))
    posts_table = FakeTable("posts", [posts_user_id])

    ref_forward = FakeRef(">", [posts_user_id], [users_id], posts_table, users_table)
    ref_reverse = FakeRef("<", [posts_user_id], [users_id], posts_table, users_table)

    class FakeParsed:
        refs = [ref_forward, ref_reverse]
        tables = [users_table, posts_table]

    monkeypatch.setattr(parser_module, "PyDBML", lambda _text: FakeParsed())

    dbml = """
    Table users {
        id integer [default: 2]
    }
    Table posts {
        user_id integer
    }
    """
    tables = parser_module.parse_dbml(dbml)

    users = next(t for t in tables if t.name == "users")
    posts = next(t for t in tables if t.name == "posts")

    assert users.note == "users note"
    assert users.columns[0].note == "id note"
    assert users.columns[0].type == "integer"
    assert users.columns[0].default == 2
    assert posts.columns[0].references == [("users", "id")]
    assert users.columns[0].references == [("posts", "user_id")]


def test_parse_dbml_enums_pydbml_branch(monkeypatch):
    dbml = """
    Enum status {
        active
        disabled
    }
    """

    monkeypatch.setattr(parser_module, "_parse_dbml_enums_from_text", lambda _text: {})
    enums = parser_module.parse_dbml_enums(dbml)

    assert enums["status"] == ["active", "disabled"]


def test_parse_field_kwargs_and_annotation_to_type():
    source = """
from typing import Optional
import models
import module

DESCRIPTIONS = {"name": "User name"}
EXTRA = {"description": "Extra"}
VALUE = "x"
key = "name"
Team = object()


def factory():
    return "x"


class User:
    name: str = Field(description=DESCRIPTIONS["name"], unique=True)
    missing: str = Field(description=OTHER["missing"])
    name_key: str = Field(description=DESCRIPTIONS[key])
    optional_ref: Optional[models.Team] = Field(default=None)
    simple_opt: Optional[Team] = Field(default=None)
    direct_ref: models.Team = Field(default=None)
    alias: str = Field(default=VALUE)
    attr: str = Field(default=module.VALUE)
    extra: str = Field(**EXTRA)
    created: str = Field(default_factory=lambda: "x")
    called: str = Field(default=factory())
    weird: tuple[int, int] = Field(default=None)
"""
    tree = ast.parse(source)
    class_node = next(node for node in tree.body if isinstance(node, ast.ClassDef))
    kwargs = []
    first_call = None
    for node in class_node.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Call):
            if first_call is None:
                first_call = node.value
            kwargs.append(_parse_field_kwargs(node.value, {"DESCRIPTIONS": {"name": "User name"}}))

    assert any(item.get("description") == "User name" for item in kwargs)
    assert any(item.get("unique") is True for item in kwargs)
    assert first_call is not None
    _parse_field_kwargs(first_call)

    opt_node = next(
        node
        for node in class_node.body
        if isinstance(node, ast.AnnAssign) and node.target.id == "optional_ref"
    )
    simple_opt = next(
        node
        for node in class_node.body
        if isinstance(node, ast.AnnAssign) and node.target.id == "simple_opt"
    )
    direct_node = next(
        node
        for node in class_node.body
        if isinstance(node, ast.AnnAssign) and node.target.id == "direct_ref"
    )
    weird_node = next(
        node
        for node in class_node.body
        if isinstance(node, ast.AnnAssign) and node.target.id == "weird"
    )

    assert _annotation_to_type(opt_node.annotation) == ("Team", True)
    assert _annotation_to_type(simple_opt.annotation) == ("Team", True)
    assert _annotation_to_type(direct_node.annotation) == ("Team", False)
    assert _annotation_to_type(weird_node.annotation) == ("str", False)


def test_extract_columns_edge_cases():
    source = """
from sqlmodel import Field, Relationship

class Model:
    id: int
    raw: int = 1
    rel: "Other" = Relationship()
    skip: int = Other()
    ok: int = Field(default=1)
"""
    tree = ast.parse(source)
    class_node = next(node for node in tree.body if isinstance(node, ast.ClassDef))

    columns = _extract_columns(class_node, None)
    names = {col.name for col in columns}
    assert "id" in names
    assert "ok" in names
    assert "raw" not in names
    assert "rel" not in names
    assert "skip" not in names


def test_parse_model_file_missing_table_class(tmp_path):
    model_path = _write_model(tmp_path, "models/user/model.py", "class Base: pass")
    with pytest.raises(ValueError):
        _parse_model_file(model_path, {})


def test_parse_model_file_duplicate_columns(tmp_path):
    model_py = """
from sqlmodel import Field, SQLModel

class Base(SQLModel):
    id: int = Field(primary_key=True)

class User(Base, table=True):
    id: int = Field(primary_key=True)
"""
    model_path = _write_model(tmp_path, "models/user/model.py", model_py)
    table = _parse_model_file(model_path, {})
    assert len([c for c in table.columns if c.name == "id"]) == 1


def test_sqlmodel_to_dbml_generate_and_apply(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    enums_py = """
from enum import Enum

class Status(Enum):
    __dbml_name__ = "status"
    ACTIVE = "active"

class NotEnum:
    pass
"""
    _write_model(tmp_path, "models/enums.py", enums_py)

    model_py = """
from typing import Optional
import models
from sqlmodel import Field, SQLModel, Relationship

DESCRIPTIONS = {"name": "User name"}
EXTRA = {"description": "Extra"}


def factory():
    return "x"


class Base(SQLModel):
    id: int = Field(primary_key=True)


class User(Base, table=True):
    '''User table.'''
    name: str = Field(description=DESCRIPTIONS["name"], unique=True)
    other: str = Field(description=OTHER["missing"])
    status: Status = Field(default="active")
    team_id: Optional[models.Team] = Field(default=None, foreign_key="teams.id")
    extra: str = Field(**EXTRA)
    created: str = Field(default_factory=lambda: "x")
    called: str = Field(default=factory())
    rel: list["Team"] = Relationship(back_populates="users")
"""
    _write_model(tmp_path, "models/user/model.py", model_py)
    teams_py = """
from sqlmodel import Field, SQLModel

class Team(SQLModel, table=True):
    id: int = Field(primary_key=True)
"""
    _write_model(tmp_path, "models/teams/model.py", teams_py)

    dbml = generate_dbml_from_models(models_dir)
    assert "Table user" in dbml
    assert "status status" in dbml
    assert "ref: > teams.id" in dbml
    assert 'note: "User name"' in dbml

    schema_dbml = """
    Table teams {
        id integer [pk]
    }
    Table user {
        id integer [pk, default: 10]
        name text
        status text
        team_id integer
    }
    """
    hinted = apply_schema_hints(dbml, schema_dbml)
    assert "default: 10" in hinted
    assert "status text" in hinted


def test_sqlmodel_to_dbml_helpers_and_changes():
    col = ColumnInfo(
        name="name",
        type="text",
        primary_key=False,
        unique=True,
        nullable=False,
        default="bob",
        references=[("teams", "id")],
        note='note "quoted"',
    )
    formatted = _format_dbml_column(col)
    assert 'default: "bob"' in formatted
    assert "ref: > teams.id" in formatted
    assert 'note: "note \\"quoted\\""' in formatted

    header = _format_table_header_like("table users {", TableInfo("users", [], note="hi"))
    header_caps = _format_table_header_like("Table users {", TableInfo("users", []))
    header_full = _format_table_header(TableInfo("users", [], note="hi"))
    header_plain = _format_table_header(TableInfo("users", []))
    assert header.startswith("table users")
    assert header_caps == "Table users {"
    assert "note:" in header_full
    assert header_plain == "Table users {"

    assert _canonical_dbml_type("serial4") == "integer"
    assert _canonical_dbml_type("CUSTOM") == "custom"
    assert _columns_equivalent(col, col) is True

    plain_col = ColumnInfo(
        name="id",
        type="integer",
        primary_key=False,
        unique=False,
        nullable=True,
    )
    assert _format_dbml_column(plain_col) == "  id integer"
    num_default = ColumnInfo(
        name="count",
        type="integer",
        primary_key=False,
        unique=False,
        nullable=True,
        default=5,
    )
    assert "default: 5" in _format_dbml_column(num_default)

    existing = """
Table legacy {
  id integer [primary key]
}

Table users [note: \"Old note\"] {
  id integer [primary key]
  name text
  // keep
}
"""
    generated = """
Table users [note: \"New note\"] {
  id integer [primary key]
  name text [not null]
}

Table teams {
  id integer [primary key]
}
"""
    updated = apply_dbml_changes(existing, generated)
    assert "New note" in updated
    assert "// keep" in updated
    assert "Table teams" in updated

    updated_tables = apply_dbml_table_updates(existing, generated)
    assert "not null" in updated_tables

    canonical = canonicalize_dbml_text("Table users {\n  id serial4\n}\n")
    assert "id integer" in canonical
    assert "Note: keep" in canonicalize_dbml_text("Note: keep\n")

    assert normalize_dbml("Table users {\n  id integer [pk]\n}\n")
    assert normalize_dbml_for_compare("Table users {\n  id serial4 [pk]\n}\n")


def test_columns_equivalent_false_cases():
    base = ColumnInfo(
        name="id",
        type="integer",
        primary_key=False,
        unique=False,
        nullable=True,
        default=None,
        references=None,
        note=None,
    )
    assert _columns_equivalent(base, ColumnInfo(**{**base.__dict__, "type": "text"})) is False
    assert _columns_equivalent(base, ColumnInfo(**{**base.__dict__, "primary_key": True})) is False
    assert _columns_equivalent(base, ColumnInfo(**{**base.__dict__, "unique": True})) is False
    assert _columns_equivalent(base, ColumnInfo(**{**base.__dict__, "nullable": False})) is False
    assert _columns_equivalent(base, ColumnInfo(**{**base.__dict__, "default": 1})) is False
    assert (
        _columns_equivalent(base, ColumnInfo(**{**base.__dict__, "references": [("t", "id")]}))
        is False
    )
    assert _columns_equivalent(base, ColumnInfo(**{**base.__dict__, "note": "x"})) is False


def test_apply_dbml_table_updates_unchanged_block():
    dbml = """
    Table users {
        id integer [pk]
    }
    """
    updated = apply_dbml_table_updates(dbml, dbml)
    assert "Table users" in updated


def test_sqlmodel_to_dbml_model_files_helpers(tmp_path):
    models_dir = tmp_path / "models"
    assert list(_model_files(models_dir)) == []

    models_dir.mkdir()
    file_path = _write_model(tmp_path, "models/users/model.py", "class User: ...")
    assert list(_model_files(models_dir)) == [file_path]
    assert _table_name_from_path(file_path) == "users"


def test_generate_dbml_from_models_no_files(tmp_path):
    with pytest.raises(ValueError):
        generate_dbml_from_models(tmp_path / "models")


def test_commands_preview_info_generate(tmp_path):
    schema_file = tmp_path / "schema.dbml"
    schema_file.write_text(_dbml_sample_tables(), encoding="utf-8")

    output = tmp_path / "out"
    output.mkdir()

    generated_files = generate_all_files(schema_file.read_text(encoding="utf-8"))

    for rel_path, content in generated_files.items():
        if not rel_path.endswith("/model.py"):
            continue
        file_path = output / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if "users" in rel_path:
            file_path.write_text(content, encoding="utf-8")
        elif "teams" in rel_path:
            file_path.write_text(content + "\nEXTRA = 1\n", encoding="utf-8")
        elif "projects" in rel_path:
            file_path.write_text(USER_FILE_MARKER + "\n" + content, encoding="utf-8")
        else:
            pass

    summary = preview.preview_command(
        schema_file=schema_file, output=output, show_all=True, show_new=True
    )
    assert summary["new"] >= 1
    assert summary["modified"] >= 1
    assert summary["protected"] >= 1

    preview.preview_command(schema_file=schema_file, output=output, show_all=False, show_new=False)

    info.info_command(schema_file=schema_file, output=output)

    generate.generate_command(
        schema_file=schema_file, output=output, force=False, admin_auth_enabled=False
    )

    generate.generate_command(
        schema_file=schema_file, output=output, force=True, admin_auth_enabled=True
    )


def test_commands_generate_all_files_errors(tmp_path, monkeypatch):
    schema_file = tmp_path / "schema.dbml"
    schema_file.write_text("Table users {\n  id integer [pk]\n}\n", encoding="utf-8")

    def raise_generate(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(preview, "generate_all_files", raise_generate)
    with pytest.raises(typer.Exit):
        preview.preview_command(schema_file=schema_file, output=tmp_path)

    monkeypatch.setattr(info, "generate_all_files", raise_generate)
    with pytest.raises(typer.Exit):
        info.info_command(schema_file=schema_file, output=tmp_path)

    monkeypatch.setattr(generate, "generate_all_files", raise_generate)
    with pytest.raises(typer.Exit):
        generate.generate_command(schema_file=schema_file, output=tmp_path)


def test_commands_error_paths(tmp_path, monkeypatch):
    schema_file = tmp_path / "schema.dbml"
    schema_file.write_text("Table users { id integer [pk] }", encoding="utf-8")

    def bad_read(*_args, **_kwargs):
        raise OSError("boom")

    monkeypatch.setattr(Path, "read_text", bad_read)

    with pytest.raises(typer.Exit):
        preview.preview_command(schema_file=schema_file)

    with pytest.raises(typer.Exit):
        info.info_command(schema_file=schema_file)

    with pytest.raises(typer.Exit):
        generate.generate_command(schema_file=schema_file)


def test_code_to_dbml_command_branches(tmp_path):
    schema_file = tmp_path / "schema.dbml"

    with pytest.raises(Exception):
        code_to_dbml.code_to_dbml_command(schema_file=schema_file, output=tmp_path)

    models_dir = tmp_path / "out" / "models"
    models_dir.mkdir(parents=True)
    _write_model(tmp_path, "out/models/enums.py", "from enum import Enum\n")
    model_py = """
from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
"""
    _write_model(tmp_path, "out/models/user/model.py", model_py)

    generated, existing, changed = code_to_dbml.code_to_dbml_command(
        schema_file=schema_file,
        output=tmp_path / "out",
    )
    assert existing == ""
    assert changed is True
    assert "Table user" in generated

    schema_file.write_text(generated, encoding="utf-8")
    _generated2, existing2, changed2 = code_to_dbml.code_to_dbml_command(
        schema_file=schema_file,
        output=tmp_path / "out",
    )
    assert existing2
    assert changed2 is False


def test_diff_helpers(tmp_path, monkeypatch):
    diff_module.print_diff("", "file.txt")
    diff_module.print_diff("-a\n+b", "file.txt")

    file_path = tmp_path / "file.txt"
    assert diff_module.apply_diff_to_file(file_path, "old", "new") is True
    assert file_path.read_text(encoding="utf-8") == "new"

    assert diff_module.apply_diff_to_file(file_path, "new", "new") is False

    original_generate_diff = diff_module.generate_diff
    monkeypatch.setattr(diff_module, "generate_diff", lambda *_args, **_kwargs: "")
    file_path.write_text("old", encoding="utf-8")
    assert diff_module.apply_diff_to_file(file_path, "old", "new") is False

    monkeypatch.setattr(diff_module, "generate_diff", original_generate_diff)

    file_path.write_text("a\nb\nc\n", encoding="utf-8")
    assert diff_module.apply_diff_to_file(file_path, "a\nb\nc\n", "a\nx\nc\n") is True

    file_path.write_text("z\nb\ny\n", encoding="utf-8")
    assert diff_module.apply_diff_to_file(file_path, "a\nb\nc\n", "a\nx\nc\n") is True

    file_path.write_text("a\nb\nz\nc\nd\n", encoding="utf-8")
    assert diff_module.apply_diff_to_file(file_path, "a\nb\nc\nd\n", "a\nx\ny\nd\n") is True

    file_path.write_text("q\nw\n", encoding="utf-8")
    assert diff_module.apply_diff_to_file(file_path, "a\nb\n", "a\nx\n") is False

    file_path.write_text("", encoding="utf-8")
    assert diff_module.apply_diff_to_file(file_path, "", "a\n") is False

    class Boom(Exception):
        pass

    def raise_patch(_text):
        raise Boom("fail")

    monkeypatch.setattr(diff_module, "PatchSet", raise_patch)
    assert diff_module.apply_diff_to_file(file_path, "a\n", "b\n") is False
