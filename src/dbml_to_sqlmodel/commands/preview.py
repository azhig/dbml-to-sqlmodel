"""Preview command - show diff of changes without writing files."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..generator import generate_all_files
from ..utils import (
    calculate_file_status,
    generate_diff,
    normalize_model_code,
    print_diff,
    print_file_status_table,
)

console = Console()


def preview_command(
    schema_file: Annotated[
        Path, typer.Argument(help="Path to DBML schema file", exists=True, dir_okay=False)
    ],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output directory")] = Path(
        "output"
    ),
    show_all: Annotated[bool, typer.Option("--all", "-a", help="Show unchanged files too")] = False,
    show_new: Annotated[
        bool, typer.Option("--new", "-n", help="Show content of new files")
    ] = False,
):
    """Preview changes without writing files (shows diff)."""
    console.print(
        Panel(
            f"[bold cyan]Preview mode - showing diffs[/bold cyan]\n"
            f"Schema: [green]{schema_file}[/green]\n"
            f"Output: [yellow]{output}[/yellow]",
            border_style="cyan",
        )
    )

    # Read DBML file
    try:
        dbml_content = schema_file.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[red]Error reading schema file:[/red] {e}")
        raise typer.Exit(1) from e

    # Generate files
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Parsing DBML schema...", total=None)
            generated_files = generate_all_files(dbml_content)
            progress.update(task, description=f"Generated {len(generated_files)} files")

    except Exception as e:
        console.print(f"[red]Error generating files:[/red] {e}")
        raise typer.Exit(1) from e

    # Focus preview on model.py files only
    generated_files = {
        rel_path: content
        for rel_path, content in generated_files.items()
        if rel_path.endswith("/model.py")
    }

    # Calculate file status
    file_status = calculate_file_status(output, generated_files, normalizer=normalize_model_code)

    # Print status table
    console.print()
    if show_all:
        table_status = file_status
    else:
        table_status = {k: v for k, v in file_status.items() if v[0] != "unchanged"}
    print_file_status_table(table_status)
    console.print()

    # Show diffs
    for rel_path, content in sorted(generated_files.items()):
        file_path = output / rel_path
        status, is_protected = file_status[rel_path]

        # Skip unchanged files unless --all is specified
        if status == "unchanged" and not show_all:
            continue

        # Show protected file warning
        if is_protected:
            console.print(
                Panel(
                    "[yellow]Protected file (USER_MODIFIED)[/yellow]\n"
                    "This file will be skipped during generation unless --force is used",
                    title=f"[bold yellow]{rel_path}[/bold yellow]",
                    border_style="yellow",
                )
            )
            console.print()
            continue

        # Show diff for modified files
        if status == "modified":
            old_content = normalize_model_code(file_path.read_text(encoding="utf-8"))
            new_content = normalize_model_code(content)
            diff = generate_diff(old_content, new_content, rel_path)
            print_diff(diff, rel_path)
            console.print()

        # Show new file content if requested
        elif status == "created" and show_new:
            console.print(
                Panel(
                    f"[green]New file ({len(content)} bytes)[/green]\n"
                    f"Use --new flag to see full content",
                    title=f"[bold green]{rel_path}[/bold green]",
                    border_style="green",
                )
            )
            console.print()

        elif status == "created":
            console.print(f"[green]New file:[/green] {rel_path} ({len(content)} bytes)")

    # Summary
    new_files = sum(1 for s, _ in file_status.values() if s == "created")
    modified_files = sum(1 for s, _ in file_status.values() if s == "modified")
    unchanged_files = sum(1 for s, _ in file_status.values() if s == "unchanged")
    protected_files = sum(1 for _, p in file_status.values() if p)

    console.print(
        Panel(
            f"[bold cyan]Preview Summary[/bold cyan]\n\n"
            f"New files: [green]{new_files}[/green]\n"
            f"Modified files: [blue]{modified_files}[/blue]\n"
            f"Unchanged files: [dim]{unchanged_files}[/dim]\n"
            f"Protected files: [yellow]{protected_files}[/yellow]",
            border_style="cyan",
        )
    )

    return {
        "new": new_files,
        "modified": modified_files,
        "unchanged": unchanged_files,
        "protected": protected_files,
    }
