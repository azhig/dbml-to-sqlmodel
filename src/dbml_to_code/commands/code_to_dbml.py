"""Generate DBML from generated SQLModel code."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from ..sqlmodel_to_dbml import (
    apply_schema_hints,
    generate_dbml_from_models,
    normalize_dbml,
    normalize_dbml_for_compare,
)
from ..utils import generate_diff, print_diff

console = Console()


def code_to_dbml_command(
    schema_file: Annotated[Path, typer.Argument(help="Path to DBML schema file")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output directory")] = Path("output"),
) -> tuple[str, str, bool]:
    """Generate DBML from output models, show diff, and return normalized DBML."""
    models_dir = output / "models"
    if not models_dir.exists():
        raise typer.BadParameter(f"Models directory not found: {models_dir}")

    generated_dbml = generate_dbml_from_models(models_dir)

    if schema_file.exists():
        existing = schema_file.read_text(encoding="utf-8")
        generated_dbml = apply_schema_hints(generated_dbml, existing)
        normalized_generated = normalize_dbml(generated_dbml)
        compare_generated = normalize_dbml_for_compare(generated_dbml)
        normalized_existing = normalize_dbml(existing)
        compare_existing = normalize_dbml_for_compare(existing)

        # Show diff between normalized versions (structural changes only)
        diff = generate_diff(normalized_existing, normalized_generated, schema_file.name)
        print_diff(diff, schema_file.name)

        changed = compare_existing != compare_generated
    else:
        normalized_generated = normalize_dbml(generated_dbml)
        console.print(Panel(
            Syntax(normalized_generated, "text", theme="monokai", line_numbers=False),
            title=f"[bold green]{schema_file.name}[/bold green]",
            border_style="green",
            expand=False,
        ))
        changed = True
        normalized_existing = ""

    return normalized_generated, normalized_existing, changed
