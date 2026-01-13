"""File management utilities."""

from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from ..constants import USER_FILE_MARKER, PROTECTED_FILE_WARNING


def is_user_modified(file_path: Path) -> bool:
    """Check if file contains user modification marker.

    Args:
        file_path: Path to file to check

    Returns:
        True if file contains USER_MODIFIED marker
    """
    if not file_path.exists():
        return False

    content = file_path.read_text(encoding="utf-8")
    return USER_FILE_MARKER in content


def mark_as_user_modified(file_path: Path) -> None:
    """Add user modification marker to file.

    Args:
        file_path: Path to file to mark
    """
    if not file_path.exists():
        return

    content = file_path.read_text(encoding="utf-8")
    if USER_FILE_MARKER not in content:
        content = PROTECTED_FILE_WARNING + "\n" + content
        file_path.write_text(content, encoding="utf-8")


def get_user_modified_files(output_dir: Path) -> List[Path]:
    """Get list of user-modified files in output directory.

    Args:
        output_dir: Output directory to scan

    Returns:
        List of paths to user-modified Python files
    """
    if not output_dir.exists():
        return []

    user_files = []
    for file_path in output_dir.rglob("*.py"):
        if is_user_modified(file_path):
            user_files.append(file_path)

    return user_files


def calculate_file_status(
    output_dir: Path,
    generated_files: Dict[str, str],
    normalizer: Optional[Callable[[str], str]] = None,
) -> Dict[str, Tuple[str, bool]]:
    """Calculate status for each file to be generated.

    Args:
        output_dir: Output directory path
        generated_files: Dict mapping relative file path to content
        normalizer: Optional function to normalize content for comparison

    Returns:
        Dict mapping filename to (status, is_user_modified) tuple
        where status is one of: "created", "modified", "unchanged", "protected"
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
