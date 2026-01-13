"""Utility functions for CLI."""

import ast
import difflib
from pathlib import Path
from typing import Dict, List, Tuple

from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.table import Table
from unidiff import PatchSet

console = Console()

# Marker to detect user-modified files
USER_FILE_MARKER = "# USER_MODIFIED"
PROTECTED_FILE_WARNING = """# USER_MODIFIED
# This file has been manually modified and is protected from regeneration.
# Remove this marker if you want to allow regeneration.
"""


def is_user_modified(file_path: Path) -> bool:
    """Check if file contains user modification marker."""
    if not file_path.exists():
        return False

    content = file_path.read_text(encoding="utf-8")
    return USER_FILE_MARKER in content


def mark_as_user_modified(file_path: Path) -> None:
    """Add user modification marker to file."""
    if not file_path.exists():
        return

    content = file_path.read_text(encoding="utf-8")
    if USER_FILE_MARKER not in content:
        content = PROTECTED_FILE_WARNING + "\n" + content
        file_path.write_text(content, encoding="utf-8")


def get_user_modified_files(output_dir: Path) -> List[Path]:
    """Get list of user-modified files in output directory."""
    if not output_dir.exists():
        return []

    user_files = []
    for file_path in output_dir.rglob("*.py"):
        if is_user_modified(file_path):
            user_files.append(file_path)

    return user_files


def generate_diff(original: str, modified: str, filename: str) -> str:
    """Generate unified diff between two strings."""
    diff = difflib.unified_diff(
        original.splitlines(keepends=False),
        modified.splitlines(keepends=False),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm="",
    )
    return "\n".join(diff)


def apply_diff_to_file(file_path: Path, original: str, modified: str) -> bool:
    """
    Apply diff between original and modified to the actual file.

    This function computes the diff and applies it as a patch to preserve
    formatting and structure that may differ between original and the file.

    Args:
        file_path: Path to the file to patch
        original: Original content (normalized/compared version)
        modified: Modified content (new version)

    Returns:
        True if changes were applied, False if no changes
    """
    if not file_path.exists():
        # File doesn't exist, just write the modified version
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(modified, encoding="utf-8")
        return True

    current = file_path.read_text(encoding="utf-8")

    # If content is identical, no need to apply changes
    if current.strip() == modified.strip():
        return False

    # Generate unified diff
    diff_text = generate_diff(original, modified, file_path.name)

    if not diff_text:
        return False

    try:
        patch = PatchSet(diff_text)
        current_lines = current.splitlines()

        def find_block(haystack: list[str], block: list[str]) -> int | None:
            if not block:
                return None
            for idx in range(len(haystack) - len(block) + 1):
                if haystack[idx:idx + len(block)] == block:
                    return idx
            return None

        applied_any = False
        for patched_file in patch:
            for hunk in patched_file:
                old_block = [line.value.rstrip("\n") for line in hunk if line.is_context or line.is_removed]
                new_block = [line.value.rstrip("\n") for line in hunk if line.is_context or line.is_added]

                start_idx = find_block(current_lines, old_block)
                if start_idx is not None:
                    current_lines[start_idx:start_idx + len(old_block)] = new_block
                    applied_any = True
                    continue

                removed_lines = [line.value.rstrip("\n") for line in hunk if line.is_removed]
                added_lines = [line.value.rstrip("\n") for line in hunk if line.is_added]

                if removed_lines:
                    seq_idx = find_block(current_lines, removed_lines)
                    if seq_idx is not None:
                        current_lines[seq_idx:seq_idx + len(removed_lines)] = added_lines
                        applied_any = True
                        continue

                if removed_lines and added_lines and len(removed_lines) == len(added_lines):
                    for removed, added in zip(removed_lines, added_lines):
                        try:
                            line_idx = current_lines.index(removed)
                        except ValueError:
                            continue
                        current_lines[line_idx] = added
                        applied_any = True

        if not applied_any:
            console.print("[yellow]Warning: Could not match diff hunks to file content; no changes applied.[/yellow]")
            return False

        patched_content = "\n".join(current_lines)
        if current.endswith("\n"):
            patched_content += "\n"
        file_path.write_text(patched_content, encoding="utf-8")
        return True

    except Exception as e:
        console.print(f"[yellow]Warning: Could not apply patch cleanly: {e}[/yellow]")
        console.print(f"[yellow]Error details: {type(e).__name__}: {e}[/yellow]")
        return False


def print_diff(diff_text: str, filename: str) -> None:
    """Print colorized diff using rich."""
    if not diff_text:
        console.print(f"[green]OK[/green] {filename} - no changes")
        return

    console.print(Panel(
        Syntax(diff_text, "diff", theme="monokai", line_numbers=False),
        title=f"[bold cyan]{filename}[/bold cyan]",
        border_style="cyan",
        expand=False,
    ))


def normalize_model_code(text: str) -> str:
    """Normalize model code to ignore formatting-only differences."""
    try:
        tree = ast.parse(text)
        return ast.unparse(tree).strip()
    except SyntaxError:
        lines = [line.rstrip() for line in text.splitlines()]
        lines = [line for line in lines if line.strip()]
        return "\n".join(lines)


def print_file_status_table(files_status: Dict[str, Tuple[str, bool]]) -> None:
    """
    Print table with file status.

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


def calculate_file_status(
    output_dir: Path,
    generated_files: Dict[str, str],
    normalizer=None,
) -> Dict[str, Tuple[str, bool]]:
    """
    Calculate status for each file to be generated.

    Args:
        output_dir: Output directory path
        generated_files: Dict mapping relative file path to content

    Returns:
        Dict mapping filename to (status, is_user_modified)
    """
    status = {}

    for rel_path, new_content in generated_files.items():
        file_path = output_dir / rel_path
        is_protected = is_user_modified(file_path)

        if is_protected:
            status[rel_path] = ("protected", True)
        elif not file_path.exists():
            status[rel_path] = ("created", False)
        else:
            old_content = file_path.read_text(encoding="utf-8")
            if normalizer:
                old_content = normalizer(old_content)
                new_content = normalizer(new_content)
            if old_content.strip() == new_content.strip():
                status[rel_path] = ("unchanged", False)
            else:
                status[rel_path] = ("modified", False)

    return status
