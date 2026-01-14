"""Generate command - create FastAPI application from DBML schema."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from ..generator import generate_all_files
from ..utils import (
    calculate_file_status,
    print_file_status_table,
)

console = Console()


def generate_command(
    schema_file: Annotated[
        Path, typer.Argument(help="Path to DBML schema file", exists=True, dir_okay=False)
    ],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output directory")] = Path(
        "output"
    ),
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite user-modified files")
    ] = False,
    admin_auth_enabled: Annotated[
        bool,
        typer.Option(
            "--admin-auth/--no-admin-auth",
            help="Require login for SQLAdmin panel",
        ),
    ] = False,
):
    """Generate FastAPI application from DBML schema."""
    config_table = Table.grid(padding=(0, 2))
    config_table.add_column(style="bold cyan")
    config_table.add_column()

    config_table.add_row("Schema:", f"[white]{schema_file}[/white]")
    config_table.add_row("Output:", f"[yellow]{output}[/yellow]")
    config_table.add_row(
        "Admin Auth:", "[green]Enabled[/green]" if admin_auth_enabled else "[dim]Disabled[/dim]"
    )
    if force:
        config_table.add_row(
            "Force Mode:", "[red]ON[/red] [dim](will overwrite protected files)[/dim]"
        )

    console.print()
    console.print(
        Panel(
            config_table,
            title="[bold cyan]Generating FastAPI Application[/bold cyan]",
            border_style="cyan",
            subtitle="[dim]Building your API...[/dim]",
        )
    )
    console.print()

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
            generated_files = generate_all_files(
                dbml_content, admin_auth_enabled=admin_auth_enabled
            )
            progress.update(task, description=f"Generated {len(generated_files)} files")

    except Exception as e:
        console.print(f"[red]Error generating files:[/red] {e}")
        raise typer.Exit(1) from e

    # Calculate file status
    file_status = calculate_file_status(output, generated_files)

    # Check for protected files
    protected_files = [f for f, (status, protected) in file_status.items() if protected]

    if protected_files and not force:
        console.print("\n[yellow]Protected files detected:[/yellow]")
        for file in protected_files:
            console.print(f"  [protected] {file}")
        console.print(
            "\n[yellow]These files contain the USER_MODIFIED marker and will be skipped.[/yellow]\n"
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
        TextColumn("[bold blue]{task.description}"),
        BarColumn(complete_style="green", finished_style="bold green"),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Writing files...", total=len(generated_files))

        for rel_path, content in generated_files.items():
            file_path = output / rel_path
            _status, is_protected = file_status[rel_path]

            # Skip protected files unless force is enabled
            if is_protected and not force:
                skipped_count += 1
                progress.update(task, description=f"[yellow]Skipping protected: {rel_path}")
                progress.advance(task)
                continue

            # Create parent directory
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            file_path.write_text(content, encoding="utf-8")
            written_count += 1
            progress.update(task, description=f"[green]Writing: {rel_path}")
            progress.advance(task)

        progress.update(task, description="[bold green]✓ All files written")

    # Summary with fancy box
    console.print()
    summary_table = Table.grid(padding=(0, 2))
    summary_table.add_column(style="bold")
    summary_table.add_column(style="cyan")

    summary_table.add_row("> Files written:", f"[bold green]{written_count}[/bold green]")
    if skipped_count > 0:
        summary_table.add_row("> Files skipped:", f"[yellow]{skipped_count}[/yellow]")
    summary_table.add_row("> Output directory:", f"[cyan]{output.absolute()}[/cyan]")

    console.print(
        Panel(
            summary_table,
            title="[bold green]Generation Complete[/bold green]",
            border_style="green",
            subtitle="[dim]Ready to deploy[/dim]",
        )
    )

    # Next steps
    console.print()
    console.print("[bold cyan]Next steps:[/bold cyan]")
    console.print(f"  [dim]1.[/dim] [white]cd {output}[/white]")
    console.print("  [dim]2.[/dim] [white]uv run python main.py[/white]")
    console.print(
        "  [dim]3.[/dim] [white]Open[/white] [blue underline]http://localhost:8001/admin[/blue underline]"
    )
    console.print()
