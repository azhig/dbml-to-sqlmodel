"""Generate command - create FastAPI application from DBML schema."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..generator import generate_all_files
from ..utils import (
    calculate_file_status,
    is_user_modified,
    print_file_status_table,
)

console = Console()


def generate_command(
    schema_file: Annotated[Path, typer.Argument(help="Path to DBML schema file", exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output directory")] = Path("output"),
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite user-modified files")] = False,
):
    """Generate FastAPI application from DBML schema."""
    console.print(Panel(
        f"[bold cyan]Generating FastAPI Application[/bold cyan]\n"
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
        raise typer.Exit(1)

    # Calculate file status
    file_status = calculate_file_status(output, generated_files)

    # Check for protected files
    protected_files = [f for f, (status, protected) in file_status.items() if protected]

    if protected_files and not force:
        console.print("\n[yellow]⚠️  Protected files detected:[/yellow]")
        for file in protected_files:
            console.print(f"  🔒 {file}")
        console.print(
            "\n[yellow]These files contain USER_MODIFIED marker and will be skipped.[/yellow]\n"
            "[yellow]Use --force to overwrite them anyway.[/yellow]"
        )

    # Print status table
    console.print()
    print_file_status_table(file_status)

    # Write files
    output.mkdir(parents=True, exist_ok=True)
    written_count = 0
    skipped_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Writing files...", total=len(generated_files))

        for rel_path, content in generated_files.items():
            file_path = output / rel_path
            status, is_protected = file_status[rel_path]

            # Skip protected files unless force is enabled
            if is_protected and not force:
                skipped_count += 1
                progress.advance(task)
                continue

            # Create parent directory
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            file_path.write_text(content, encoding="utf-8")
            written_count += 1
            progress.advance(task)

    # Summary
    console.print(
        Panel(
            f"[bold green]✓ Generation complete![/bold green]\n\n"
            f"Files written: [green]{written_count}[/green]\n"
            f"Files skipped: [yellow]{skipped_count}[/yellow]\n"
            f"Output directory: [cyan]{output.absolute()}[/cyan]\n\n"
            f"[dim]Next steps:[/dim]\n"
            f"  1. cd {output}\n"
            f"  2. uv run python main.py\n"
            f"  3. Open http://localhost:8001/admin",
            border_style="green",
        )
    )
