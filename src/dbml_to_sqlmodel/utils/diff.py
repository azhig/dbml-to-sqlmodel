"""Diff and patching utilities."""

import ast
import difflib
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from unidiff import PatchSet

console = Console()


def normalize_model_code(text: str) -> str:
    """Normalize model code to ignore formatting-only differences.

    Uses AST parsing to normalize Python code structure.

    Args:
        text: Python source code

    Returns:
        Normalized code string
    """
    try:
        tree = ast.parse(text)
        return ast.unparse(tree).strip()
    except SyntaxError:
        # Fallback: simple normalization
        lines = [line.rstrip() for line in text.splitlines()]
        lines = [line for line in lines if line.strip()]
        return "\n".join(lines)


def generate_diff(original: str, modified: str, filename: str) -> str:
    """Generate unified diff between two strings.

    Args:
        original: Original content
        modified: Modified content
        filename: Filename for diff header

    Returns:
        Unified diff as string
    """
    diff = difflib.unified_diff(
        original.splitlines(keepends=False),
        modified.splitlines(keepends=False),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm="",
    )
    return "\n".join(diff)


def print_diff(diff_text: str, filename: str) -> None:
    """Print colorized diff using rich.

    Args:
        diff_text: Unified diff text
        filename: Filename for title
    """
    if not diff_text:
        console.print(f"[green]OK[/green] {filename} - no changes")
        return

    console.print(
        Panel(
            Syntax(diff_text, "diff", theme="monokai", line_numbers=False),
            title=f"[bold cyan]{filename}[/bold cyan]",
            border_style="cyan",
            expand=False,
        )
    )


def apply_diff_to_file(file_path: Path, original: str, modified: str) -> bool:
    """Apply diff between original and modified to the actual file.

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
            """Find exact block of lines in haystack."""
            if not block:
                return None
            for idx in range(len(haystack) - len(block) + 1):
                if haystack[idx : idx + len(block)] == block:
                    return idx
            return None

        applied_any = False
        for patched_file in patch:
            for hunk in patched_file:
                old_block = [
                    line.value.rstrip("\n") for line in hunk if line.is_context or line.is_removed
                ]
                new_block = [
                    line.value.rstrip("\n") for line in hunk if line.is_context or line.is_added
                ]

                start_idx = find_block(current_lines, old_block)
                if start_idx is not None:
                    current_lines[start_idx : start_idx + len(old_block)] = new_block
                    applied_any = True
                    continue

                removed_lines = [line.value.rstrip("\n") for line in hunk if line.is_removed]
                added_lines = [line.value.rstrip("\n") for line in hunk if line.is_added]

                if removed_lines:
                    seq_idx = find_block(current_lines, removed_lines)
                    if seq_idx is not None:
                        current_lines[seq_idx : seq_idx + len(removed_lines)] = added_lines
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
            console.print(
                "[yellow]Warning: Could not match diff hunks to file content; no changes applied.[/yellow]"
            )
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
