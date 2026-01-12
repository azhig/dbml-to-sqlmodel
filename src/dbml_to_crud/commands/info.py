"""Report command - show generated files and model mismatches."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from ..generator import generate_all_files
from ..utils import (
    calculate_file_status,
    generate_diff,
    normalize_model_code,
    print_diff,
    print_file_status_table,
)

console = Console()


def info_command(
    schema_file: Annotated[Path, typer.Argument(help="Path to DBML schema file", exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output directory")] = Path("output"),
):
    """Show generated files and model mismatches."""
    console.print(Panel(
        f"[bold cyan]Report[/bold cyan]\n"
        f"Schema: [green]{schema_file}[/green]\n"
        f"Output: [yellow]{output}[/yellow]",
        border_style="cyan",
    ))

    # Read DBML file
    try:
        dbml_content = schema_file.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[red]Error reading schema file:[/red] {e}")
        raise typer.Exit(1)

    # Generate files from DBML
    try:
        generated_files = generate_all_files(dbml_content)
    except Exception as e:
        console.print(f"[red]Error generating files:[/red] {e}")
        raise typer.Exit(1)

    generated_files = {
        rel_path: content
        for rel_path, content in generated_files.items()
        if rel_path.endswith("/model.py")
    }

    file_status = calculate_file_status(output, generated_files, normalizer=normalize_model_code)

    console.print()
    print_file_status_table(file_status)
    console.print()

    for rel_path, content in sorted(generated_files.items()):
        file_path = output / rel_path
        status, is_protected = file_status[rel_path]

        if status == "unchanged":
            continue

        if is_protected:
            console.print(Panel(
                "[yellow]🔒 Protected file (USER_MODIFIED)[/yellow]\n"
                "This file will be skipped during generation unless --force is used",
                title=f"[bold yellow]{rel_path}[/bold yellow]",
                border_style="yellow",
            ))
            console.print()

        if status in {"modified", "protected"} and file_path.exists():
            old_content = normalize_model_code(file_path.read_text(encoding="utf-8"))
            new_content = normalize_model_code(content)
            diff = generate_diff(old_content, new_content, rel_path)
            print_diff(diff, rel_path)
            console.print()
        elif status == "created":
            syntax_lang = "python" if file_path.suffix == ".py" else "text"
            console.print(Panel(
                Syntax(content, syntax_lang, theme="monokai", line_numbers=False),
                title=f"[bold green]{rel_path}[/bold green]",
                border_style="green",
                expand=False,
            ))
            console.print()

    new_files = sum(1 for s, _ in file_status.values() if s == "created")
    modified_files = sum(1 for s, _ in file_status.values() if s == "modified")
    unchanged_files = sum(1 for s, _ in file_status.values() if s == "unchanged")
    protected_files = sum(1 for _, p in file_status.values() if p)

    console.print(
        Panel(
            f"[bold cyan]Report Summary[/bold cyan]\n\n"
            f"New files: [green]{new_files}[/green]\n"
            f"Modified files: [blue]{modified_files}[/blue]\n"
            f"Unchanged files: [dim]{unchanged_files}[/dim]\n"
            f"Protected files: [yellow]{protected_files}[/yellow]",
            border_style="cyan",
        )
    )
