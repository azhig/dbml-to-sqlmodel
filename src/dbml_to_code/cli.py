"""Interactive CLI for DBML to Code Generator."""

import sys
import time
from pathlib import Path

import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .commands import generate, preview, info, code_to_dbml
from .core import ConfigManager
from .sqlmodel_to_dbml import apply_dbml_table_updates

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()
config_manager = ConfigManager()

# Custom style for questionary menus with highlighted selection
custom_style = Style([
    ('qmark', 'fg:#00d7ff bold'),           # Question mark - bright cyan
    ('question', 'fg:#ffffff bold'),         # Question text - white bold
    ('answer', 'fg:#00ff87 bold'),          # Selected answer - bright green
    ('pointer', 'fg:#ffff00 bold'),         # Pointer (>) - bright yellow
    ('highlighted', 'fg:#000000 bold bg:#ffff00 underline'),  # Highlighted option - bold black on yellow with underline
    ('selected', 'fg:#00ff87'),             # Selected checkbox - green
    ('separator', 'fg:#5f5f87'),            # Separator - muted purple
    ('instruction', 'fg:#87afaf'),          # Instructions - muted cyan
    ('text', ''),                           # Plain text - default
    ('disabled', 'fg:#5f5f5f italic')       # Disabled option - gray italic
])


def show_welcome(is_first_run: bool):
    """Show welcome banner with ASCII art."""
    # ASCII art logo
    logo = """
[bold cyan]
██████╗ ██████╗ ███╗   ███╗██╗         ████████╗ ██████╗      ██████╗ ██████╗ ██████╗ ███████╗
██╔══██╗██╔══██╗████╗ ████║██║         ╚══██╔══╝██╔═══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
██║  ██║██████╔╝██╔████╔██║██║            ██║   ██║   ██║    ██║     ██║   ██║██║  ██║█████╗
██║  ██║██╔══██╗██║╚██╔╝██║██║            ██║   ██║   ██║    ██║     ██║   ██║██║  ██║██╔══╝
██████╔╝██████╔╝██║ ╚═╝ ██║███████╗       ██║   ╚██████╔╝    ╚██████╗╚██████╔╝██████╔╝███████╗
╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝       ╚═╝    ╚═════╝      ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
[/bold cyan]"""

    console.print(logo)
    console.print()

    if is_first_run:
        console.print(
            Panel(
                "[bold white]Modern FastAPI + SQLModel + FastCRUD generator from DBML schemas[/bold white]\n\n"
                "[yellow]> Welcome! This is your first run.[/yellow]\n"
                "[green]> Configuration file created: .dbml_to_code[/green]",
                border_style="cyan",
                title="[bold cyan]First Time Setup[/bold cyan]",
                subtitle="[dim]Let's get started[/dim]",
            )
        )
    else:
        console.print(
            Panel(
                "[bold white]Modern FastAPI + SQLModel + FastCRUD generator from DBML schemas[/bold white]\n\n"
                "[dim]Transform your database schemas into production-ready APIs[/dim]",
                border_style="cyan",
                title="[bold cyan]Ready[/bold cyan]",
            )
        )


def run_initial_setup():
    """Run first-time setup to populate settings."""
    config = config_manager.config

    console.print()
    console.print(
        Panel(
            "[bold white]Initial Setup[/bold white]\n\n"
            "[dim]Configure your preferences. You can change these later in the settings menu.[/dim]",
            border_style="cyan",
            title="[bold cyan]Configuration[/bold cyan]",
        )
    )
    console.print()

    schema_file = questionary.path(
        "Path to DBML schema:",
        default=config.schema_file,
    ).ask()
    output_dir = questionary.text(
        "Output directory:",
        default=config.output_dir,
    ).ask()
    show_all_files = questionary.confirm(
        "Show all files in preview?",
        default=config.show_all_files,
    ).ask()
    show_new_content = questionary.confirm(
        "Show new file contents?",
        default=config.show_new_content,
    ).ask()
    force_overwrite = questionary.confirm(
        "Overwrite protected files (USER_MODIFIED)?",
        default=config.force_overwrite,
    ).ask()
    admin_auth_enabled = questionary.confirm(
        "Require login for SQLAdmin?",
        default=config.admin_auth_enabled,
    ).ask()

    config_manager.update(
        schema_file=schema_file or config.schema_file,
        output_dir=output_dir or config.output_dir,
        show_all_files=config.show_all_files
        if show_all_files is None
        else show_all_files,
        show_new_content=config.show_new_content
        if show_new_content is None
        else show_new_content,
        force_overwrite=config.force_overwrite
        if force_overwrite is None
        else force_overwrite,
        admin_auth_enabled=config.admin_auth_enabled
        if admin_auth_enabled is None
        else admin_auth_enabled,
    )


def show_menu_header():
    """Show just the menu header without logo."""
    console.print()
    console.print(Panel(
        "[bold cyan]DBML to Code Generator[/bold cyan]",
        border_style="cyan",
    ))

def interactive_menu():
    """Show interactive menu and handle user selection."""
    is_first_run = config_manager.is_first_run()
    config_manager.load()

    # Show welcome logo only once at startup
    if is_first_run:
        show_welcome(is_first_run)
        run_initial_setup()
    else:
        show_welcome(False)

    while True:
        # Always clear screen before showing menu
        console.clear()
        show_menu_header()

        console.print()
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                questionary.Choice("[>] Settings            - Configure generator options", value="settings"),
                questionary.Choice("[>] DBML → Code         - Generate FastAPI from schema", value="generate"),
                questionary.Choice("[>] Code → DBML         - Extract schema from models", value="code_to_dbml"),
                questionary.Choice("[>] Report              - View generation statistics", value="report"),
                questionary.Choice("[x] Exit", value="exit"),
            ],
            use_shortcuts=True,
            use_arrow_keys=True,
            style=custom_style,
        ).ask()

        if choice is None or choice == "exit":
            console.clear()
            console.print()
            console.print(Panel(
                "[bold cyan]Thank you for using DBML to Code![/bold cyan]\n\n"
                "[dim]Build amazing APIs![/dim]",
                border_style="cyan",
            ))
            console.print()
            break

        # Clear screen and show compact header for results
        console.clear()
        console.print("[bold cyan]DBML to Code[/bold cyan]")
        console.print("[dim]" + "─" * console.width + "[/dim]")
        console.print()

        try:
            if choice == "settings":
                handle_settings()
            elif choice == "generate":
                handle_generate()
            elif choice == "code_to_dbml":
                handle_code_to_dbml()
            elif choice == "report":
                handle_report()
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")

        # Show separator after command results
        console.print()
        console.print("[dim]" + "─" * console.width + "[/dim]")


def handle_settings():
    """Handle settings menu."""
    config = config_manager.config

    while True:
        # Show current settings
        table = Table(
            title="Current settings", show_header=True, header_style="bold cyan"
        )
        table.add_column("Setting", style="cyan", width=30)
        table.add_column("Value", style="green")

        table.add_row("Schema file", config.schema_file)
        table.add_row("Output directory", config.output_dir)
        table.add_row("Show all files", "Yes" if config.show_all_files else "No")
        table.add_row(
            "Show new file contents", "Yes" if config.show_new_content else "No"
        )
        table.add_row(
            "Overwrite protected files", "Yes" if config.force_overwrite else "No"
        )
        table.add_row(
            "Require SQLAdmin login", "Yes" if config.admin_auth_enabled else "No"
        )

        console.print()
        console.print(table)
        console.print()

        action = questionary.select(
            "Choose action:",
            choices=[
                questionary.Choice("Edit schema file", value="schema_file"),
                questionary.Choice("Edit output directory", value="output_dir"),
                questionary.Choice("Toggle: show all files", value="show_all_files"),
                questionary.Choice(
                    "Toggle: show new file contents", value="show_new_content"
                ),
                questionary.Choice(
                    "Toggle: overwrite protected files", value="force_overwrite"
                ),
                questionary.Choice(
                    "Toggle: SQLAdmin login", value="admin_auth_enabled"
                ),
                questionary.Choice("Reset to defaults", value="reset"),
                questionary.Choice("Back to main menu", value="back"),
            ],
            use_shortcuts=True,
            use_arrow_keys=True,
            style=custom_style,
        ).ask()

        if action is None or action == "back":
            break

        if action == "reset":
            if questionary.confirm(
                "Reset all settings to defaults?", default=False
            ).ask():
                config_manager.reset()
                config = config_manager.config
                console.print("[green]Settings reset[/green]")
            continue

        if action == "schema_file":
            new_value = questionary.text(
                "Path to schema file:",
                default=config.schema_file,
            ).ask()
            if new_value:
                config_manager.update(schema_file=new_value)
                config = config_manager.config
                console.print("[green]Schema file updated[/green]")

        elif action == "output_dir":
            new_value = questionary.text(
                "Output directory:",
                default=config.output_dir,
            ).ask()
            if new_value:
                config_manager.update(output_dir=new_value)
                config = config_manager.config
                console.print("[green]Output directory updated[/green]")

        elif action in [
            "show_all_files",
            "show_new_content",
            "force_overwrite",
            "admin_auth_enabled",
        ]:
            # Toggle boolean value
            current_value = getattr(config, action)
            config_manager.update(**{action: not current_value})
            config = config_manager.config
            console.print(
                f"[green]Setting updated to: {'Yes' if not current_value else 'No'}[/green]"
            )


def handle_report():
    """Handle report command interactively."""
    config = config_manager.config

    schema_file = Path(config.schema_file)
    if not schema_file.exists():
        console.print(f"[red]Error: file not found: {schema_file}[/red]")
        return

    console.print()
    info.info_command(schema_file, output=Path(config.output_dir))


def handle_generate():
    """Handle generate command interactively."""
    config = config_manager.config

    schema_file = Path(config.schema_file)
    if not schema_file.exists():
        console.print(f"[red]Error: file not found: {schema_file}[/red]")
        return

    output_dir = Path(config.output_dir)

    # First, show preview if output directory exists
    if output_dir.exists():
        console.print(
            Panel(
                "[yellow]Output directory already exists.[/yellow]\n"
                "Showing a preview first...",
                border_style="yellow",
                title="Attention",
            )
        )
        console.print()

        # Show preview
        preview_summary = preview.preview_command(
            schema_file=schema_file,
            output=output_dir,
            show_all=config.show_all_files,
            show_new=config.show_new_content,
        )

        console.print()

        changes_count = preview_summary.get("new", 0) + preview_summary.get(
            "modified", 0
        )
        if changes_count > 0:
            if not questionary.confirm("Apply changes?", default=False).ask():
                console.print("[yellow]Generation cancelled[/yellow]")
                return
        else:
            console.print("[green]No changes detected - no confirmation needed[/green]")

    console.print()
    generate.generate_command(
        schema_file=schema_file,
        output=output_dir,
        force=config.force_overwrite,
        admin_auth_enabled=config.admin_auth_enabled,
    )


def handle_code_to_dbml():
    """Handle code -> DBML conversion interactively."""
    config = config_manager.config

    schema_file = Path(config.schema_file)
    output_dir = Path(config.output_dir)

    console.print()
    normalized_dbml, _normalized_existing, changed = code_to_dbml.code_to_dbml_command(
        schema_file=schema_file,
        output=output_dir,
    )

    if not changed:
        console.print("[green]No changes - nothing to save[/green]")
        return

    if questionary.confirm(
        f"Save DBML to {schema_file}?",
        default=False,
    ).ask():
        schema_file.parent.mkdir(parents=True, exist_ok=True)
        existing_text = (
            schema_file.read_text(encoding="utf-8") if schema_file.exists() else ""
        )
        updated_text = apply_dbml_table_updates(existing_text, normalized_dbml)
        schema_file.write_text(updated_text, encoding="utf-8")
        console.print("[green]DBML saved[/green]")


def app():
    """Main entry point for interactive CLI."""
    try:
        interactive_menu()
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting. Goodbye.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        raise


if __name__ == "__main__":
    app()
