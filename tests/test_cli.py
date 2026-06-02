"""Tests for the typer CLI layer (cli.py)."""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dbml_to_sqlmodel import cli as cli_module
from dbml_to_sqlmodel.commands import code_to_dbml, generate, info, preview


def test_cli_app_error_paths(monkeypatch):
    # Make argv deterministic so cli() does not pick up pytest's own flags.
    monkeypatch.setattr(sys, "argv", ["dbml-to-sqlmodel"])

    # KeyboardInterrupt is handled inside the callback; the standalone app then
    # exits cleanly with code 0. This also exercises the app() entry wrapper.
    def raise_keyboard():
        raise KeyboardInterrupt

    monkeypatch.setattr(cli_module, "interactive_menu", raise_keyboard)
    with pytest.raises(SystemExit) as exc_info:
        cli_module.app()
    assert exc_info.value.code in (0, None)

    # A generic exception propagates out of the callback (standalone_mode=False
    # makes click re-raise instead of converting it into a sys.exit()).
    def raise_error():
        raise ValueError("boom")

    monkeypatch.setattr(cli_module, "interactive_menu", raise_error)
    with pytest.raises(ValueError):
        cli_module.cli([], standalone_mode=False)


def test_cli_version_flag():
    """`--version` prints the version and exits with code 0."""
    with pytest.raises(SystemExit) as exc_info:
        cli_module.cli(["--version"])
    assert exc_info.value.code == 0


def test_cli_subcommand_wrappers(tmp_path, monkeypatch):
    """The typer command wrappers forward their arguments to the command layer."""
    schema = tmp_path / "schema.dbml"
    schema.write_text("Table users {\n    id integer [pk]\n}\n", encoding="utf-8")
    out = tmp_path / "out"

    calls: dict[str, dict] = {}
    monkeypatch.setattr(generate, "generate_command", lambda **kw: calls.update(generate=kw))
    monkeypatch.setattr(preview, "preview_command", lambda **kw: calls.update(preview=kw))
    monkeypatch.setattr(info, "info_command", lambda **kw: calls.update(info=kw))

    cli_module.cli(["generate", str(schema), "-o", str(out)], standalone_mode=False)
    assert calls["generate"]["schema_file"] == schema
    assert calls["generate"]["output"] == out

    cli_module.cli(["preview", str(schema), "-o", str(out)], standalone_mode=False)
    assert calls["preview"]["schema_file"] == schema

    cli_module.cli(["info", str(schema), "-o", str(out)], standalone_mode=False)
    assert calls["info"]["schema_file"] == schema


def test_cli_code_to_dbml_wrapper(tmp_path, monkeypatch):
    """code-to-dbml writes only when changes are detected."""
    source_dir = tmp_path / "out"
    source_dir.mkdir()
    target = tmp_path / "schema.dbml"

    # No changes -> the file is not written.
    monkeypatch.setattr(
        code_to_dbml, "code_to_dbml_command", lambda **kw: ("dbml", "existing", False)
    )
    cli_module.cli(["code-to-dbml", str(source_dir), "-o", str(target)], standalone_mode=False)
    assert not target.exists()

    # Changes detected -> the DBML file is written.
    generated = "Table users {\n    id integer [pk]\n}\n"
    monkeypatch.setattr(code_to_dbml, "code_to_dbml_command", lambda **kw: (generated, "", True))
    cli_module.cli(["code-to-dbml", str(source_dir), "-o", str(target)], standalone_mode=False)
    assert target.exists()
    assert "users" in target.read_text(encoding="utf-8")
