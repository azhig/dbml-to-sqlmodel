"""Tests for the reverse conversion (code -> DBML) module."""

import ast
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

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


def _write_model(tmp_path: Path, rel_path: str, content: str) -> Path:
    file_path = tmp_path / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return file_path


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
