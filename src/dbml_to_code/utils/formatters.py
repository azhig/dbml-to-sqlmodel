"""Output formatting utilities."""

from typing import Dict, Tuple

from rich.console import Console
from rich.table import Table

console = Console()


def print_file_status_table(files_status: Dict[str, Tuple[str, bool]]) -> None:
    """Print table with file status.

    Args:
        files_status: Dict mapping filename to (status, is_user_modified)
            status can be: "created", "modified", "unchanged", "protected"
    """
    table = Table(title="File Status", show_header=True, header_style="bold magenta")
    table.add_column("File", style="cyan", no_wrap=False)
    table.add_column("Status", style="white")
    table.add_column("Action", style="yellow")

    for filename, (status, is_protected) in sorted(files_status.items()):
        if is_protected:
            status_text = "Protected"
            action = "Skipped"
            style = "yellow"
        elif status == "created":
            status_text = "New"
            action = "Will create"
            style = "green"
        elif status == "modified":
            status_text = "Changed"
            action = "Will update"
            style = "blue"
        else:  # unchanged
            status_text = "Unchanged"
            action = "No action"
            style = "dim"

        table.add_row(
            filename,
            status_text,
            action,
            style=style,
        )

    console.print(table)
