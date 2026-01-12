"""Interactive CLI for DBML to CRUD Generator."""

import sys
from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .commands import generate, preview, info, code_to_dbml
from .config import ConfigManager
from .sqlmodel_to_dbml import apply_dbml_table_updates

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()
config_manager = ConfigManager()


def show_welcome(is_first_run: bool):
    """Show welcome banner."""
    if is_first_run:
        console.print(Panel(
            "[bold cyan]🚀 DBML to CRUD Generator[/bold cyan]\n\n"
            "Modern FastAPI + SQLModel + FastCRUD generator from DBML schemas\n\n"
            "[yellow]Добро пожаловать! Это первый запуск.[/yellow]\n"
            "Создан файл конфигурации: [green].dbml_to_crud[/green]",
            border_style="cyan",
            title="Welcome",
        ))
    else:
        console.print(Panel(
            "[bold cyan]🚀 DBML to CRUD Generator[/bold cyan]\n\n"
            "Modern FastAPI + SQLModel + FastCRUD generator from DBML schemas",
            border_style="cyan",
            title="Welcome",
        ))


def run_initial_setup():
    """Run first-time setup to populate settings."""
    config = config_manager.config

    console.print(Panel(
        "[bold cyan]Первичная настройка[/bold cyan]\n"
        "Эти параметры можно изменить позже в меню настроек.",
        border_style="cyan",
    ))

    schema_file = questionary.path(
        "Путь к DBML схеме:",
        default=config.schema_file,
    ).ask()
    output_dir = questionary.text(
        "Директория вывода:",
        default=config.output_dir,
    ).ask()
    show_all_files = questionary.confirm(
        "Показывать все файлы в preview?",
        default=config.show_all_files,
    ).ask()
    show_new_content = questionary.confirm(
        "Показывать содержимое новых файлов?",
        default=config.show_new_content,
    ).ask()
    force_overwrite = questionary.confirm(
        "Перезаписывать защищенные файлы (USER_MODIFIED)?",
        default=config.force_overwrite,
    ).ask()

    config_manager.update(
        schema_file=schema_file or config.schema_file,
        output_dir=output_dir or config.output_dir,
        show_all_files=config.show_all_files if show_all_files is None else show_all_files,
        show_new_content=config.show_new_content if show_new_content is None else show_new_content,
        force_overwrite=config.force_overwrite if force_overwrite is None else force_overwrite,
    )


def interactive_menu():
    """Show interactive menu and handle user selection."""
    is_first_run = config_manager.is_first_run()
    config_manager.load()

    show_welcome(is_first_run)
    if is_first_run:
        run_initial_setup()

    while True:
        choice = questionary.select(
            "Что вы хотите сделать?",
            choices=[
                questionary.Choice("⚙️  Настройки", value="settings"),
                questionary.Choice("🎯 DBML → Code", value="generate"),
                questionary.Choice("🔁 Code → DBML", value="code_to_dbml"),
                questionary.Choice("📊 Report", value="report"),
                questionary.Choice("❌ Выход", value="exit"),
            ],
            use_shortcuts=True,
            use_arrow_keys=True,
        ).ask()

        if choice is None or choice == "exit":
            console.print("\n[yellow]Завершение работы. До свидания! 👋[/yellow]")
            break

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
            console.print("\n[yellow]Операция отменена[/yellow]")
            continue
        except Exception as e:
            console.print(f"\n[red]Ошибка: {e}[/red]")
            continue


def handle_settings():
    """Handle settings menu."""
    config = config_manager.config

    while True:
        # Show current settings
        table = Table(title="⚙️  Текущие настройки", show_header=True, header_style="bold cyan")
        table.add_column("Параметр", style="cyan", width=30)
        table.add_column("Значение", style="green")

        table.add_row("Файл схемы", config.schema_file)
        table.add_row("Директория вывода", config.output_dir)
        table.add_row("Показывать все файлы", "✓ Да" if config.show_all_files else "✗ Нет")
        table.add_row("Показывать содержимое новых файлов", "✓ Да" if config.show_new_content else "✗ Нет")
        table.add_row("Перезаписывать защищенные файлы", "✓ Да" if config.force_overwrite else "✗ Нет")

        console.print()
        console.print(table)
        console.print()

        action = questionary.select(
            "Выберите действие:",
            choices=[
                questionary.Choice("📝 Изменить файл схемы", value="schema_file"),
                questionary.Choice("📁 Изменить директорию вывода", value="output_dir"),
                questionary.Choice("👁️  Переключить: показывать все файлы", value="show_all_files"),
                questionary.Choice("📄 Переключить: показывать содержимое новых файлов", value="show_new_content"),
                questionary.Choice("🔒 Переключить: перезаписывать защищенные файлы", value="force_overwrite"),
                questionary.Choice("🔄 Сбросить настройки по умолчанию", value="reset"),
                questionary.Choice("⬅️  Назад в главное меню", value="back"),
            ],
            use_shortcuts=True,
            use_arrow_keys=True,
        ).ask()

        if action is None or action == "back":
            break

        if action == "reset":
            if questionary.confirm("Сбросить все настройки по умолчанию?", default=False).ask():
                config_manager.reset()
                config = config_manager.config
                console.print("[green]✓ Настройки сброшены[/green]")
            continue

        if action == "schema_file":
            new_value = questionary.text(
                "Путь к файлу схемы:",
                default=config.schema_file,
            ).ask()
            if new_value:
                config_manager.update(schema_file=new_value)
                config = config_manager.config
                console.print("[green]✓ Файл схемы обновлен[/green]")

        elif action == "output_dir":
            new_value = questionary.text(
                "Директория вывода:",
                default=config.output_dir,
            ).ask()
            if new_value:
                config_manager.update(output_dir=new_value)
                config = config_manager.config
                console.print("[green]✓ Директория вывода обновлена[/green]")

        elif action in ["show_all_files", "show_new_content", "force_overwrite"]:
            # Toggle boolean value
            current_value = getattr(config, action)
            config_manager.update(**{action: not current_value})
            config = config_manager.config
            console.print(f"[green]✓ Параметр изменен на: {'Да' if not current_value else 'Нет'}[/green]")


def handle_report():
    """Handle report command interactively."""
    config = config_manager.config

    schema_file = Path(config.schema_file)
    if not schema_file.exists():
        console.print(f"[red]Ошибка: файл {schema_file} не найден[/red]")
        return

    console.print()
    info.info_command(schema_file, output=Path(config.output_dir))


def handle_generate():
    """Handle generate command interactively."""
    config = config_manager.config

    schema_file = Path(config.schema_file)
    if not schema_file.exists():
        console.print(f"[red]Ошибка: файл {schema_file} не найден[/red]")
        return

    output_dir = Path(config.output_dir)

    # First, show preview if output directory exists
    if output_dir.exists():
        console.print(Panel(
            "[yellow]Директория вывода уже существует.[/yellow]\n"
            "Сначала показываем предпросмотр изменений...",
            border_style="yellow",
            title="⚠️  Внимание",
        ))
        console.print()

        # Show preview
        preview_summary = preview.preview_command(
            schema_file=schema_file,
            output=output_dir,
            show_all=config.show_all_files,
            show_new=config.show_new_content,
        )

        console.print()

        changes_count = (
            preview_summary.get("new", 0)
            + preview_summary.get("modified", 0)
        )
        if changes_count > 0:
            if not questionary.confirm(
                "Применить изменения?",
                default=False
            ).ask():
                console.print("[yellow]Генерация отменена[/yellow]")
                return
        else:
            console.print("[green]Изменений не обнаружено — подтверждение не требуется[/green]")

    console.print()
    generate.generate_command(
        schema_file=schema_file,
        output=output_dir,
        force=config.force_overwrite,
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
        console.print("[green]Изменений нет — сохранение не требуется[/green]")
        return

    if questionary.confirm(
        f"Сохранить DBML в {schema_file}?",
        default=False,
    ).ask():
        schema_file.parent.mkdir(parents=True, exist_ok=True)
        existing_text = schema_file.read_text(encoding="utf-8") if schema_file.exists() else ""
        updated_text = apply_dbml_table_updates(existing_text, normalized_dbml)
        schema_file.write_text(updated_text, encoding="utf-8")
        console.print("[green]✓ DBML сохранен[/green]")


def app():
    """Main entry point for interactive CLI."""
    try:
        interactive_menu()
    except KeyboardInterrupt:
        console.print("\n[yellow]Завершение работы. До свидания! 👋[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Неожиданная ошибка: {e}[/red]")
        raise


if __name__ == "__main__":
    app()
