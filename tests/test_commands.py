"""Tests for the command layer (commands/*.py)."""

import sys
from pathlib import Path

import pytest
import typer

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dbml_to_sqlmodel.commands import code_to_dbml, generate, info, preview
from dbml_to_sqlmodel.constants import USER_FILE_MARKER
from dbml_to_sqlmodel.generator import generate_all_files


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
